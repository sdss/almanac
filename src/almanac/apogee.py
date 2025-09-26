import os
import numpy as np
from glob import glob
from subprocess import check_output
from astropy.table import Table, hstack, unique
from itertools import groupby
from typing import Optional, Tuple, Dict, List, Set, Generator, Any, Union

from almanac import utils  # ensures the Yanny table reader/writer is registered
from almanac.config import config
from almanac.logger import logger
from scipy.spatial.distance import cdist

from almanac.data_models import Exposure
from almanac.data_models.utils import mjd_to_exposure_prefix, get_exposure_path

def get_unique_exposure_paths(paths: List[str]) -> List[Tuple[str, List[bool]]]:
    """
    Process a list of file paths to find unique exposures and determine which chips are available.

    :param paths:
        List of file paths to APOGEE exposure files.

    :returns:
        List of tuples containing (path_to_exposure, list_of_chip_availability).
    """

    chip_mapping = {}
    for path in paths:
        _, observatory, mjd, basename = path.rsplit("/", 3)
        prefix, chip, exposure_apz = basename.split("-")

        key = (observatory, mjd, exposure_apz)
        chip_mapping.setdefault(key, [prefix, [False, False, False]])
        index = "abc".index(chip)
        chip_mapping[key][1][index] = True

    unique_exposure_paths = []
    for (observatory, mjd, exposure_apz), (prefix, chips) in chip_mapping.items():
        chip = "abc"[chips.index(True)]
        path = f"{config.apogee_dir}/{observatory}/{mjd}/{prefix}-{chip}-{exposure_apz}"
        unique_exposure_paths.append(path)

    return unique_exposure_paths


def get_exposures(observatory: str, mjd: int) -> Generator[Exposure, None, None]:
    """
    Generate exposures taken from a given observatory on a given MJD.

    :param observatory:
        The observatory name (e.g. "apo").

    :param mjd:
        The Modified Julian Date.

    :yields:
        Exposure instances for each unique exposure found on disk.
    """
    paths = glob(get_exposure_path(observatory, mjd, "a?R", "*", "*"))
    return organize_exposures(map(Exposure.from_path, get_unique_exposure_paths(paths)))


def get_expected_number_of_exposures(observatory: str, mjd: int) -> int:
    """
    Query the SDSS database to get the expected exposures for a given observatory and MJD.
    This is useful for identifying missing exposures.
    """

    if mjd < int(getattr(config.sdssdb_exposure_min_mjd, observatory)):
        return -1

    from almanac.database import opsdb
    from peewee import fn

    for model in (opsdb.Exposure, opsdb.ExposureFlavor):
        model._meta.schema = f"opsdb_{observatory}"

    start, end = map(mjd_to_exposure_prefix, (mjd, mjd + 1))

    q = (
        opsdb.Exposure.select(
            fn.max(opsdb.Exposure.exposure_no)
        )
        .where(
            (opsdb.Exposure.exposure_no > start)
        &   (opsdb.Exposure.exposure_no < end)
        )
        .join(
            opsdb.ExposureFlavor,
            on=(opsdb.ExposureFlavor.pk == opsdb.Exposure.exposure_flavor),
        )
    )
    try:
        return q.scalar() - start
    except:
        return -1


def organize_exposures(exposures: List[Exposure]) -> List[Exposure]:
    """
    Identify any missing exposures (based on non-contiguous exposure numbers)
    and fill them with missing image types.

    :param exposures:
        A list of `Exposure` instances.

    :returns:
        A list of organized `Exposure` instances.
    """

    exposures = sorted(exposures, key=lambda x: x.exposure)

    if len(exposures) == 0:
        return []

    observatory, mjd = (exposures[0].observatory, exposures[0].mjd)

    n_expected = get_expected_number_of_exposures(observatory, mjd)
    max_exposure = max(exposures[-1].exposure, n_expected)

    organized = []
    for i in range(1, max_exposure + 1):
        if exposures and exposures[0].exposure == i:
            organized.append(exposures.pop(0))
        else:
            organized.append(
                Exposure(
                    observatory=observatory,
                    exposure=i,
                    mjd=mjd,
                    image_type="missing"
                )
            )
    return organized


def get_sequences(exposures: List[Exposure], image_type: str, fields: Tuple[str, ...]) -> List[Tuple[int, int]]:
    """
    Get exposure number ranges for sequences of a specific image type.

    :param exposures:
        Astropy Table containing exposure metadata.
    :param image_type:
        The image type to search for (e.g., "Object", "ArcLamp").
    :param fields:
        Tuple of column names to group exposures by.
    :param require_contiguous:
        Whether to require exposure numbers to be contiguous within groups.

    :returns:
        List of tuples containing (start_exposure, end_exposure) for each sequence.
    """
    s = list(filter(lambda x: x.image_type == image_type, exposures))
    sequence_exposure_numbers = []
    for v, group in groupby(s, key=lambda x: tuple(getattr(x, f) for f in fields)):
        for si, ei in utils.group_contiguous([e.exposure for e in group]):
            sequence_exposure_numbers.append((si, ei))
    return sequence_exposure_numbers


def get_arclamp_sequences(exposures: List[Exposure]) -> List[Tuple[int, int]]:
    """
    Return a list of tuples indicating the start and end exposure numbers for
    a sequence of arc lamp exposures.

    :param exposures:
        A list of `Exposure` instances.

    :returns:
        List of tuples containing (start_exposure, end_exposure) for each arc lamp sequence.
    """
    return get_sequences(exposures, "arclamp", ("dithpix", ))


def get_science_sequences(exposures: List[Exposure]) -> List[Tuple[int, int]]:
    """
    Return a list of tuples indicating the start and end exposure numbers for
    a sequence of science exposures.

    :param exposures:
        A list of `Exposure` instances.

    :returns:
        List of tuples containing (start_exposure, end_exposure) for each science sequence.
    """
    return get_sequences(exposures, "object", ("field_id", "plate_id", "config_id", "image_type"))



def get_almanac_data(observatory: str, mjd: int, fibers: bool = False, meta: bool = False):
    """
    Return comprehensive almanac data for all exposures taken from a given observatory on a given MJD.

    :param observatory:
        The observatory name (e.g. "apo").
    :param mjd:
        The Modified Julian Date.
    :param fibers:
        Whether to include fiber mapping information.
    :param xmatch:
        Whether to perform cross-matching with catalog database.
    :param kwargs:
        Additional keyword arguments passed to other functions.

    :returns:
        Tuple containing:
        - observatory name
        - MJD
        - list of warning/info messages
        - Table of exposure data
        - dictionary of sequence indices
        - dictionary of fiber mappings
    """

    exposures = get_exposures(observatory, mjd)
    exposure_sequences = {
        "objects": get_science_sequences(exposures),
        "arclamps": get_arclamp_sequences(exposures),
    }
    if fibers:
        catalogids, twomass_designations = (set(), set())
        # We only need to get targets for one exposure in each science sequence.
        for si, ei in exposure_sequences["objects"]:
            exposure = exposures[si - 1]
            if exposure.fps:
                for target in exposure.targets:
                    if target.expected_to_be_assigned_sdss_id:
                        catalogids.add(target.catalogid)
            else:
                assert NotImplementedError("Plate targets not implemented yet.")
                for target in exposure.targets:
                    twomass_designations.add(target_id_to_designation(target.target_id))

        if meta:
            # We will often run `get_almanac_data` in parallel (through multiple processes),
            # so here we are avoiding opening a database connection until the child process starts.
            from almanac.database import is_database_available, catalogdb

            sdss_id_given_catalogid = {}
            sdss_id_given_twomass_designation = {}
            if catalogids and is_database_available:
                q = (
                    catalogdb.SDSS_ID_flat
                    .select(
                        catalogdb.SDSS_ID_flat.sdss_id,
                        catalogdb.SDSS_ID_flat.catalogid
                    )
                    .where(
                        catalogdb.SDSS_ID_flat.catalogid.in_(tuple(catalogids))
                    &   (catalogdb.SDSS_ID_flat.rank == 1)
                    )
                    .tuples()
                )
                for sdss_id, catalogid in q:
                    sdss_id_given_catalogid[catalogid] = sdss_id

            if twomass_designations and is_database_available:
                q = (
                    catalogdb.SDSS_ID_flat
                    .select(
                        catalogdb.SDSS_ID_flat.sdss_id,
                        catalogdb.TwoMassPSC.designation
                    )
                    .join(
                        catalogdb.CatalogToTwoMassPSC,
                        on=(
                            catalogdb.SDSS_ID_flat.catalogid
                            == catalogdb.CatalogToTwoMassPSC.catalogid
                        ),
                    )
                    .join(
                        catalogdb.TwoMassPSC,
                        on=(
                            catalogdb.CatalogToTwoMassPSC.target_id
                            == catalogdb.TwoMassPSC.pts_key
                        ),
                    )
                    .where(
                        catalogdb.TwoMassPSC.designation.in_(
                            tuple(twomass_designations)
                        )
                    )
                    .tuples()
                )
                for sdss_id, designation in q:
                    sdss_id_given_twomass_designation[designation] = sdss_id

            # Add sdss_id to targets
            for si, ei in exposure_sequences["objects"]:
                for i in range(si - 1, ei):
                    exposure = exposures[i]
                    if exposure.fps:
                        for target in exposure.targets:
                            target.sdss_id = sdss_id_given_catalogid.get(target.catalogid, -1)
                    else:
                        for target in exposure.targets:
                            target.sdss_id = sdss_id_given_twomass_designation.get(
                                target_id_to_designation(target.target_id), -1
                            )
            raise a

    assert len(exposures) > 0
    #if len(exposures) == 0:
    #    return (observatory, mjd, messages, None, None, None)

    #exposures = Table(rows=list(exposures))

    raise a
    fiber_maps = dict(fps={}, plates={})
    if fibers:
        configids = set(exposures["configid"]).difference({"", "-1", "-999", None})
        logger.debug(f"{observatory}/{mjd} checking fibers")
        catalogids, fps_fiber_maps = get_fiber_mappings(
            get_fps_targets, configids, observatory
        )
        logger.debug(f"{observatory}/{mjd} has {len(catalogids)} unique catalogids")

        # Matching to the correct plate requires us to know which version of the
        # plate was plugged. This is stored in the `name` header in the exposure
        plate_fiber_maps = {}
        for plate_id, name in unique(exposures["plateid", "name"]):
            assert plate_id not in plate_fiber_maps, "Contact Andy, he will cry."
            if plate_id in {"", "0", "-1"}:
                continue
            plate_fiber_maps[plate_id] = get_plate_targets(observatory, mjd, plate_id, name)


        logger.debug(f"{observatory}/{mjd} has {len(twomass_designations)} unique 2mass designations")

        fiber_maps["fps"].update(fps_fiber_maps)
        fiber_maps["plates"].update(plate_fiber_maps)

        if xmatch and is_database_available:
            # Do a single database query and match [2mass/catalogid] -> sdss_id
            # Match fps first.
            logger.debug(f"{observatory}/{mjd} doing catalogid/sdss id cross-match")
            if catalogids:
                sdss_id_lookup = {}
                q = (
                    catalogdb.SDSS_ID_flat.select(
                        catalogdb.SDSS_ID_flat.sdss_id, catalogdb.SDSS_ID_flat.catalogid
                    )
                    .where(
                        catalogdb.SDSS_ID_flat.catalogid.in_(tuple(catalogids))
                        & (catalogdb.SDSS_ID_flat.rank == 1)
                    )
                    .tuples()
                )
                for sdss_id, catalogid in q:
                    sdss_id_lookup[catalogid] = sdss_id

                for config_id, targets in fiber_maps["fps"].items():
                    for target in targets:
                        target["sdss_id"] = sdss_id_lookup.get(target["catalogid"], -1)

            logger.debug(f"{observatory}/{mjd} doing 2mass/sdss id cross-match")

            # Now match any plate targets.
            if twomass_designations:
                sdss_id_lookup = {}
                q = (
                    catalogdb.SDSS_ID_flat.select(
                        catalogdb.SDSS_ID_flat.sdss_id, catalogdb.TwoMassPSC.designation
                    )
                    .join(
                        catalogdb.CatalogToTwoMassPSC,
                        on=(
                            catalogdb.SDSS_ID_flat.catalogid
                            == catalogdb.CatalogToTwoMassPSC.catalogid
                        ),
                    )
                    .join(
                        catalogdb.TwoMassPSC,
                        on=(
                            catalogdb.CatalogToTwoMassPSC.target_id
                            == catalogdb.TwoMassPSC.pts_key
                        ),
                    )
                    .where(
                        catalogdb.TwoMassPSC.designation.in_(
                            tuple(twomass_designations)
                        )
                    )
                    .tuples()
                )
                for sdss_id, designation in q:
                    sdss_id_lookup[designation] = sdss_id
                for plate_id, targets in fiber_maps["plates"].items():
                    for target in targets:
                        target["sdss_id"] = sdss_id_lookup.get(
                            target_id_to_designation(target["target_id"]), -1
                        )

    for fiber_type, mappings in fiber_maps.items():
        for refid, targets in mappings.items():
            fiber_maps[fiber_type][refid] = Table(rows=targets)
    return (observatory, mjd, messages, exposures, sequence_indices, fiber_maps)
