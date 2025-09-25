import os
import numpy as np
from glob import glob
from subprocess import check_output
from itertools import starmap
from astropy.table import Table, hstack, unique
from typing import Optional, Tuple, Dict, List, Set, Generator, Any, Union

from almanac import utils  # ensures the Yanny table reader/writer is registered
from almanac.config import config
from almanac.logger import logger
from scipy.spatial.distance import cdist


def mjd_to_exposure_prefix(mjd: int) -> int:
    """
    Convert Modified Julian Date to exposure prefix.

    :param mjd:
        Modified Julian Date.

    :returns:
        Exposure prefix number.
    """
    return (int(mjd) - 55_562) * 10_000



def match_planned_to_plugged(plate_hole_path, plug_map_path, tol=1e-5):

    planned = Table.read(plate_hole_path, format="yanny", tablename="STRUCT1")
    plugged = Table.read(plug_map_path, format="yanny", tablename="PLUGMAPOBJ")

    ra_dist = cdist(
        planned["target_ra"].reshape((-1, 1)),
        plugged["ra"].reshape((-1, 1)),
    )
    dec_dist = cdist(
        planned["target_dec"].reshape((-1, 1)),
        plugged["dec"].reshape((-1, 1)),
    )

    meets_tolerance = (ra_dist < tol) & (dec_dist < tol)
    n_matches_to_plugged_holes = np.sum(meets_tolerance, axis=0)

    has_match = (n_matches_to_plugged_holes == 1)
    N = np.sum(n_matches_to_plugged_holes > 1)
    if N > 0:
        logger.warning(
            f"{N} plugged holes match multiple planned holes on plate {plate_id}! "
            f"Following indices are all 1-indexed."
        )
        for plugged_index in np.where(n_matches_to_plugged_holes > 1)[0]:
            n = n_matches_to_plugged_holes[plugged_index]
            for i, planned_index in enumerate(np.where(meets_tolerance[:, plugged_index])[0], start=1):
                logger.warning(
                    f"Plugged hole index {plugged_index + 1} match {i + 1}/{n} within {tol:.1e} has plugged "
                    f"coordinates (ra={plugged_holes['ra'][plugged_index]:.5f}, dec={plugged_holes['dec'][plugged_index]:.5f}) "
                    f"matched to planned coordinates (ra={planned_holes['target_ra'][planned_index]:.5f}, dec={planned_holes['target_dec'][planned_index]:.5f})."
                )

    dist = np.sqrt(ra_dist**2 + dec_dist**2)
    planned_hole_indices = np.argmin(dist[:, has_match], axis=0)

    rows = hstack(
        [
            plugged[has_match],
            planned[planned_hole_indices]
        ],
        metadata_conflicts="silent",
        uniq_col_name="{table_name}{col_name}",
        table_names=("", "planned_")
    )
    return (planned, plugged, rows)


def get_headers(path, head=20_000):
    keys = (
        "DATE-OBS", "FIELDID", "DESIGNID", "CONFIGID", "SEEING", "EXPTYPE",
        "NREAD", "IMAGETYP", "LAMPQRTZ", "LAMPTHAR", "LAMPUNE", "FOCUS",
        "NAME", "PLATEID", "CARTID", "MAPID", "PLATETYP", "OBSCMT",
        "COLLPIST", "COLPITCH", "DITHPIX", "TCAMMID", "TLSDETB",
    )
    keys_str = "|".join(keys)

    commands = " | ".join(
        ['hexdump -n {head} -e \'80/1 "%_p" "\\n"\' {path}', 'egrep "{keys_str}"']
    ).format(head=head, path=path, keys_str=keys_str)
    outputs = check_output(commands, shell=True, text=True)
    outputs = outputs.strip().split("\n")

    values = _parse_headers(outputs, keys)
    return dict(zip(map(str.lower, keys), values))



def _parse_headers(output: List[str], keys: Tuple[str, ...], default=None) -> List[str]:
    """
    Parse hexdump output to extract header key-value pairs.

    :param output:
        List of strings from hexdump output containing header information.
    :param keys:
        Tuple of header keys to look for in the output.
    :param default:
        Default value to use when a key is not found.

    :returns:
        List of header values corresponding to the input keys, with defaults for missing keys.
    """
    meta = [default] * len(keys)
    for line in output:
        try:
            key, value = line.split("=", 2)
        except ValueError:  # grep'd something in the data
            continue

        key = key.strip()
        if key in keys:
            index = keys.index(key)
            if "/" in value:
                # could be comment
                *parts, comment = value.split("/")
                value = "/".join(parts)

            value = value.strip("' ")
            meta[index] = value.strip()
    return meta






def input_id_to_designation(input_id: str) -> Tuple[str, str]:
    """
    Convert an input ID to a standardized designation format.

    The input identifier might be a 2MASS-style designation (in many different
    formats), or a Gaia DR2-style designation, or an input catalog identifier.

    :param input_id:
        The input ID string.

    :returns:
        A two-length tuple containing the designation type, and the cleaned
        designation identifier.
    """
    cleaned = str(input_id).strip().lower()
    if cleaned == "na":
        return ("", "")
    is_gaia = cleaned.startswith("gaia")
    if is_gaia:
        dr, source_id = cleaned.split(" ")
        dr = dr.split("_")[1].lstrip("dr")
        return (f"Gaia_DR{dr}", source_id)

    is_twomass = cleaned.startswith("2m") or input_id.startswith("j")
    if is_twomass:
        if cleaned.startswith("2mass"):
            cleaned = cleaned[5:]
        if cleaned.startswith("2m"):
            cleaned = cleaned[2:]
        designation = str(cleaned.lstrip("-jdb_"))
        return ("2MASS", designation)
    else:
        try:
            catalogid = np.int64(cleaned)
        except:
            return ("Unknown", input_id)
        else:
            return ("catalog", cleaned)






def target_id_to_designation(target_id: str) -> str:
    """
    Convert a target ID to a standardized designation format.

    :param target_id:
        The target ID string, typically in format like '2MASS-J...' or similar.

    :returns:
        Cleaned designation string with prefixes removed.
    """
    # The target_ids seem to be styled '2MASS-J...'
    target_id = target_id.strip()
    target_id = target_id[5:] if target_id.startswith("2MASS") else target_id
    target_id = str(target_id.lstrip("-Jdb_"))
    return target_id


def get_plugMapP_path(plate_id: int) -> str:
    plate_id = int(plate_id)
    # TODO: why does the plugmap path use n digits instead of 6 like plateHole?
    path = f"{config.platelist_dir}/{str(plate_id)[:-2].zfill(4)}XX/{plate_id:0>6.0f}/plPlugMapP-{plate_id:.0f}.par"
    logger.debug(f"PlugMap path: {path}")
    return path


def get_exposure_metadata(observatory: str, mjd: int, **kwargs) -> Generator[Dict[str, Any], None, None]:
    """
    Return a generator of metadata for all exposures taken from a given observatory on a given MJD.

    :param observatory:
        The observatory name (e.g. "apo").
    :param mjd:
        The Modified Julian Date.
    :param kwargs:
        Additional keyword arguments passed to _get_meta function.

    :yields:
        Dictionary containing exposure metadata for each exposure found.
    """

    paths = glob(f"{config.apogee_dir}/{observatory}/{mjd}/a?R-*.apz")
    yield from starmap(_get_meta, get_unique_exposure_paths(paths))


def organize_exposures(
    exposures: List[Dict[str, Any]],
    expected_exposures: Optional[Dict[int, Dict[str, Any]]] = None,
    require_exposures_start_at_1: bool = True,
    **kwargs
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Identify any missing exposures (based on non-contiguous exposure numbers) and fill them with missing image types.

    :param exposures:
        List of exposure dictionaries containing metadata.
    :param expected_exposures:
        Dictionary mapping exposure numbers to expected exposure metadata.
    :param require_exposures_start_at_1:
        Whether to require exposure numbering to start at 1.
    :param kwargs:
        Additional keyword arguments to include in missing exposure template.

    :returns:
        Tuple containing the organized list of exposures and list of warning messages.
    """
    expected_exposures = expected_exposures or dict()
    missing_row_template = dict(
        prefix="apR",
        chip="",
        readout_chip_a=False,
        readout_chip_b=False,
        readout_chip_c=False,
        fieldid="-1",
        designid="-1",
        configid="-1",
        seeing="",
        exptype="MISSING",
        nread="0",
        imagetyp="Missing",
        lampqrtz="F",
        lampthar="F",
        lampune="F",
        focus="",
        name="",
        plateid="",
        cartid=-1,
        mapid="",
        platetyp="",
        obscmt="",
        collpist="",
        colpitch="",
        dithpix="",
        tcammid="",
        tlsdetb="",
        path_exists=False,
    )
    missing_row_template.update(kwargs)

    def prepare_missing_exposure(n, observatory=None, mjd=None):
        is_expected = n in expected_exposures
        if is_expected:
            missing = {**missing_row_template, **expected_exposures.pop(n)}
        else:
            missing = dict(
                exposure=n, observatory=observatory, mjd=mjd, **missing_row_template
            )

        observatory = observatory or missing["observatory"]
        mjd = mjd or missing["mjd"]

        if is_expected:
            context = f"Exposure record exists in {observatory} operations database."
        elif mjd < cutoff:
            context = f"No exposure record in {observatory} operations database because it is before MJD cutoff ({mjd} < {cutoff})."
        else:
            context = f"No exposure record in {observatory} operations database, but it should ({mjd} > {cutoff})!"

        message = f"Missing exposure {n} from {observatory} on MJD {mjd} (exptype={missing['exptype']}; configid={missing['configid']})! {context}"

        return missing, message

    corrected, messages = ([], [])
    last_exposure_id = 0
    for i, exposure in enumerate(sorted(exposures, key=lambda x: x["exposure"])):
        if i == 0:
            last_exposure_id = exposure["exposure"]
            if require_exposures_start_at_1:
                # Here the 0000 is because later we do a range that starts from
                # `last_exposure_id + 1` (e.g., the one after the current exposure)
                # But here we start at 0000 so that if the first exposure
                last_exposure_id = int(str(last_exposure_id)[:4] + "0000")

        observatory, mjd = (exposure["observatory"], exposure["mjd"])
        cutoff = int(getattr(config.sdssdb_exposure_min_mjd, observatory))

        for n in range(last_exposure_id + 1, exposure["exposure"]):
            missing, message = prepare_missing_exposure(n, observatory, mjd)
            corrected.append(missing)
            messages.append(message)

        expected_exposures.pop(exposure["exposure"], None)
        corrected.append({**missing_row_template, **exposure})
        last_exposure_id = exposure["exposure"]

    # If there are no `exposures`, but many `expected_exposures` then we find ourselves here.
    for n in sorted(expected_exposures.keys()):
        missing, message = prepare_missing_exposure(n)
        corrected.append(missing)
        messages.append(message)

    # Ensure they really are sorted.
    return (sorted(corrected, key=lambda x: x["exposure"]), messages)


def mjd_to_exposure_prefix(mjd: int) -> int:
    """
    Convert Modified Julian Date to exposure prefix.

    :param mjd:
        Modified Julian Date.

    :returns:
        Exposure prefix number.
    """
    return (mjd - 55_562) * 10_000



def get_expected_exposure_metadata(observatory: str, mjd: int) -> Dict[int, Dict]:
    """
    Query the SDSS database to get the expected exposures for a given observatory and MJD.
    This is useful for identifying missing exposures.
    """

    if mjd < int(getattr(config.sdssdb_exposure_min_mjd, observatory)):
        return dict()

    from almanac.database import opsdb

    for model in (opsdb.Exposure, opsdb.ExposureFlavor):
        model._meta.schema = f"opsdb_{observatory}"

    q = (
        opsdb.Exposure.select(
            opsdb.Exposure.exposure_no.alias("exposure"),
            opsdb.Exposure.configuration.alias("configid"),
            opsdb.ExposureFlavor.label.alias("exptype"),
            opsdb.ExposureFlavor.label.alias("imagetyp"),
            opsdb.Exposure.start_time.alias("date-obs"),
            opsdb.Exposure.comment.alias("obscmt"),
        )
        .where(
            (opsdb.Exposure.exposure_no > mjd_to_exposure_prefix(mjd))
            & (opsdb.Exposure.exposure_no < mjd_to_exposure_prefix(mjd + 1))
        )
        .join(
            opsdb.ExposureFlavor,
            on=(opsdb.ExposureFlavor.pk == opsdb.Exposure.exposure_flavor),
        )
        .dicts()
    )
    defaults = dict(observatory=observatory, mjd=mjd)
    return {r["exposure"]: {**defaults, **r} for r in q}


def get_almanac_data(observatory: str, mjd: int, fibers: bool = False, xmatch: bool = False, **kwargs) -> Tuple[str, int, List[str], Optional[Table], Optional[Dict[str, Any]], Optional[Dict[str, Dict[Union[int, str], Table]]]]:
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
    # We will often run `get_almanac_data` in parallel (through multiple processes),
    # so here we are avoiding opening a database connection until the child process starts.
    from almanac.database import is_database_available, catalogdb

    logger.debug(f"getting {observatory} for {mjd} with {fibers} {xmatch}")
    exposures_on_disk = list(get_exposure_metadata(observatory, mjd, **kwargs))
    logger.debug(f"{observatory}/{mjd} has {len(exposures_on_disk)} exposures on disk")


    # Query the database for what exposures we should have expected.
    expected_exposures = get_expected_exposure_metadata(observatory, mjd)
    logger.debug(f"{observatory}/{mjd} has {len(expected_exposures)} expected exposures")

    exposures, messages = organize_exposures(exposures_on_disk, expected_exposures)
    logger.debug(f"{observatory}/{mjd} joined: {len(exposures)}")

    if len(exposures) == 0:
        return (observatory, mjd, messages, None, None, None)

    exposures = Table(rows=list(exposures))

    sequence_indices = {
        "objects": get_object_sequence_indices(exposures),
        "arclamps": get_arclamp_sequence_indices(exposures),
    }
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


def get_sequence_exposure_numbers(
    exposures: Table,
    imagetyp: str,
    keys: Tuple[str, ...],
    require_contiguous: bool = True,
    require_path_exists: bool = True,
) -> List[Tuple[int, int]]:
    """
    Get exposure number ranges for sequences of a specific image type.

    :param exposures:
        Astropy Table containing exposure metadata.
    :param imagetyp:
        The image type to search for (e.g., "Object", "ArcLamp").
    :param keys:
        Tuple of column names to group exposures by.
    :param require_contiguous:
        Whether to require exposure numbers to be contiguous within groups.
    :param require_path_exists:
        Whether to require that the file path exists on disk.

    :returns:
        List of tuples containing (start_exposure, end_exposure) for each sequence.
    """
    mask = exposures["imagetyp"] == imagetyp
    if require_path_exists:
        mask *= exposures["path_exists"]
    exposures_ = exposures[mask]

    # if there are no exposures of type imagetyp, return an empty list
    # not returning early will cause the _group_by to fail
    if len(exposures_) == 0:
        return []
    exposures_.sort(("exposure",))
    exposures_ = exposures_.group_by(keys)

    exposure_numbers = []
    for si, ei in zip(exposures_.groups.indices[:-1], exposures_.groups.indices[1:]):
        if require_contiguous:
            sub_indices = np.hstack(
                [
                    si,
                    si + (np.where(np.diff(exposures_["exposure"][si:ei]) > 1)[0] + 1),
                    ei,
                ]
            )
            for sj, ej in zip(sub_indices[:-1], sub_indices[1:]):
                exposure_numbers.append(tuple(exposures_["exposure"][sj:ej][[0, -1]]))
        else:
            exposure_numbers.append(tuple(exposures_["exposure"][si:ei][[0, -1]]))
    return exposure_numbers


def get_arclamp_sequence_indices(exposures: Table, **kwargs) -> np.ndarray:
    """
    Get array indices for ArcLamp exposure sequences.

    :param exposures:
        Astropy Table containing exposure metadata.
    :param kwargs:
        Additional keyword arguments passed to get_sequence_exposure_numbers.

    :returns:
        Numpy array of sequence indices for ArcLamp exposures.
    """
    sequence_exposure_numbers = get_sequence_exposure_numbers(
        exposures, imagetyp="ArcLamp", keys=("dithpix",), **kwargs
    )
    sequence_indices = np.searchsorted(exposures["exposure"], sequence_exposure_numbers)
    if sequence_indices.size > 0:
        sequence_indices += [0, 1]  # to offset the end index
    return np.sort(sequence_indices, axis=0)


def get_object_sequence_indices(exposures: Table, **kwargs) -> np.ndarray:
    """
    Get array indices for Object exposure sequences.

    :param exposures:
        Astropy Table containing exposure metadata.
    :param kwargs:
        Additional keyword arguments passed to get_sequence_exposure_numbers.

    :returns:
        Numpy array of sequence indices for Object exposures.
    """
    sequence_exposure_numbers = get_sequence_exposure_numbers(
        exposures,
        imagetyp="Object",
        keys=("fieldid", "plateid", "configid", "imagetyp"),
        **kwargs,
    )
    sequence_indices = np.searchsorted(exposures["exposure"], sequence_exposure_numbers)
    if sequence_indices.size > 0:
        sequence_indices += [0, 1]  # to offset the end index
    return np.sort(sequence_indices, axis=0)


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
        unique_exposure_paths.append((path, chips))

    return unique_exposure_paths


def get_fiber_mappings(f: callable, iterable: Union[List[int], List[str]], *args) -> Tuple[Set[Union[int, str]], Dict[Union[int, str], List[Dict[str, Any]]]]:
    """
    Apply a function to get fiber mappings for multiple items and collect all unique IDs.

    :param f:
        Function to call for each item (e.g., get_fps_targets, get_plate_targets).
    :param iterable:
        Collection of items to process (config IDs, plate IDs, etc.).
    :param args:
        Additional arguments to pass to the function.

    :returns:
        Tuple containing a set of all unique IDs and a dictionary mapping items to their targets.
    """
    all_ids, mappings = (set(), {})
    for item in iterable:
        ids, mapping = f(item, *args)
        mappings[item] = mapping
        all_ids.update(ids)
    return (all_ids, mappings)
