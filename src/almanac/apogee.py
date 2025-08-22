import re
import os
import numpy as np
from glob import glob
from subprocess import check_output
from itertools import starmap
from tqdm import tqdm
from astropy.table import Table
from typing import Optional, Tuple, Dict

from almanac import utils  # ensures the Yanny table reader/writer is registered
from almanac.config import config
from almanac.logger import logger

SAS_BASE_DIR = os.environ.get("SAS_BASE_DIR", "/uufs/chpc.utah.edu/common/home/sdss/")
PLATELIST_DIR = os.environ.get(
    "PLATELIST_DIR",
    "/uufs/chpc.utah.edu/common/home/sdss09/software/svn.sdss.org/data/sdss/platelist/trunk/",
)
SDSSCORE_DIR = os.environ.get(
    "SDSSCORE_DIR",
    "/uufs/chpc.utah.edu/common/home/sdss50/software/git/sdss/sdsscore/main/",
)

YANNY_TARGET_MATCH = re.compile(
    r'STRUCT1 APOGEE_?\w* (?P<target_type>\w+) (?P<source_type>[\w-]+) (?P<target_ra>[\-\+\.\w\d+]+) (?P<target_dec>[\-\+\.\w\d+]+) \d+ \d+ \d+ (?P<fiber_id>\d+) .+ (?P<target_id>"?[\w\d\s\.\-\+]{1,29}"?) [\d ]?(?P<xfocal>[\-\+\.\w\d+]+) (?P<yfocal>[\-\+\.\w\d+]+)$'
)

RAW_HEADER_KEYS = (
    "DATE-OBS",
    "FIELDID",
    "DESIGNID",
    "CONFIGID",
    "SEEING",
    "EXPTYPE",
    "NREAD",
    "IMAGETYP",
    "LAMPQRTZ",
    "LAMPTHAR",
    "LAMPUNE",
    "FOCUS",
    "NAME",
    "PLATEID",
    "CARTID",
    "MAPID",
    "PLATETYP",
    "OBSCMT",
    "COLLPIST",
    "COLPITCH",
    "DITHPIX",
    "TCAMMID",
    "TLSDETB",
)


def _parse_hexdump_headers(output, keys, default=""):
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


def _get_meta(path, has_chips=(None, None, None), keys=RAW_HEADER_KEYS, head=20_000):
    keys_str = "|".join(keys)
    commands = " | ".join(
        ['hexdump -n {head} -e \'80/1 "%_p" "\\n"\' {path}', 'egrep "{keys_str}"']
    ).format(head=head, path=path, keys_str=keys_str)
    outputs = check_output(commands, shell=True, text=True)
    outputs = outputs.strip().split("\n")
    values = _parse_hexdump_headers(outputs, keys)
    _, observatory, mjd, basename = path.rsplit("/", 3)
    prefix, chip, exposure = basename.split("-")
    exposure = exposure.strip(".apz")
    headers = dict(
        observatory=observatory,
        mjd=int(mjd),
        exposure=int(exposure),
        prefix=prefix,
        chip=chip,
        path_exists=os.path.exists(path),
    )
    for prefix, has_chip in zip("abc", has_chips):
        headers[f"readout_chip_{prefix}"] = has_chip

    headers.update(dict(zip(map(str.lower, RAW_HEADER_KEYS), values)))
    if headers["cartid"].strip() == "FPS":
        headers["cartid"] = 0
    return headers


def target_id_to_designation(target_id):
    # The target_ids seem to be styled '2MASS-J...'
    target_id = target_id.strip()
    return (target_id[5:] if target_id.startswith("2MASS") else target_id).lstrip(
        "-Jdb_"
    )


def get_plateHole_path(plate_id):
    plate_id = int(plate_id)
    path = f"{PLATELIST_DIR}/plates/{str(plate_id)[:-2].zfill(4)}XX/{plate_id:0>6.0f}/plateHoles-{plate_id:0>6.0f}.par"
    logger.debug(f"plateHole path: {path}")
    return path


def get_plate_targets(plate_id):
    targets, count, designations = ([], 0, set())
    with open(get_plateHole_path(plate_id), "r") as fp:
        for line in fp:
            if line.startswith("STRUCT1 APOGEE"):
                target = re.match(YANNY_TARGET_MATCH, line).groupdict()
                target["target_id"] = target["target_id"].strip(' "')
                target["sdss_id"] = -1
                designations.add(target_id_to_designation(target["target_id"]))
                targets.append(target)
                count += 1
                if count == 500:
                    break

    return (designations, targets)


# get FPS plug info
def get_confSummary_path(observatory, config_id):
    # we want the confSummaryFS file. The F means that is has the actual robot positions measured
    # measured by the field view camera. The S means that that it has Jose's estimate of whether
    # unassigned APOGEE fibers can be used as sky.

    # config_ids are left-padded to 6 digits and foldered by the first 3 and first 4 digits.
    # the final file name does not used the padded config_id
    # For example config_id 1838 is in summary_files/001XXX/0018XX/confSummaryFS-1838.par
    c = str(config_id)
    directory = f"{SDSSCORE_DIR}/{observatory}/summary_files/{c[:-3].zfill(3)}XXX/{c[:-2].zfill(4)}XX/"

    # fall back to confSummary if confSummaryFS does not exist
    path = f"{directory}/confSummaryFS-{config_id}.par"
    if not os.path.exists(path):
        path = f"{directory}/confSummary-{config_id}.par"
    logger.debug(f"confSummary(FS) path: {path}")

    return path


def get_fps_targets(config_id, observatory):
    """
    Return a list of dicts containing the target information for the given `observatory` and `config_id`.

    :param config_id:
        The configuration ID.

    :param observatory:
        The observatory name (e.g. "apo").
    """
    t = Table.read(
        get_confSummary_path(observatory, config_id),
        format="yanny",
        tablename="FIBERMAP",
    )
    t["sdss_id"] = -1
    mapping = [dict(zip(t.colnames, row)) for row in t]
    return (set(t["catalogid"]), mapping)


def get_exposure_metadata(observatory: str, mjd: int, **kwargs):
    """
    Return a generator of metadata for all exposures taken from a given observatory on a given MJD.
    """

    paths = glob(f"{SAS_BASE_DIR}/sdsswork/data/apogee/{observatory}/{mjd}/a?R-*.apz")
    yield from starmap(_get_meta, get_unique_exposure_paths(paths))


def organize_exposures(
    exposures, expected_exposures=None, require_exposures_start_at_1=True, **kwargs
):
    """
    Identify any missing exposures (based on non-contiguous exposure numbers) and fill them with missing image types.
    """
    expected_exposures = expected_exposures or dict()
    missing_row_template = dict(
        # observatory=exposures["observatory"][0],
        # mjd=exposures["mjd"][0],
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

        logger.critical(
            f"Missing exposure {n} from {observatory} on MJD {mjd} (exptype={missing['exptype']}; configid={missing['configid']})! {context}"
        )

        return missing

    corrected = []
    last_exposure_id = 0
    for i, exposure in enumerate(sorted(exposures, key=lambda x: x["exposure"])):
        if i == 0:
            last_exposure_id = exposure["exposure"]
            if require_exposures_start_at_1:
                last_exposure_id = int(str(last_exposure_id)[:4] + "0001")

        observatory, mjd = (exposure["observatory"], exposure["mjd"])
        cutoff = getattr(config.sdssdb_exposure_min_mjd, observatory)

        for n in range(last_exposure_id + 1, exposure["exposure"]):
            corrected.append(prepare_missing_exposure(n, observatory, mjd))

        expected_exposures.pop(exposure["exposure"], None)         
        corrected.append({**missing_row_template, **exposure})
        last_exposure_id = exposure["exposure"]

    # If there are no `exposures`, but many `expected_exposures` then we find ourselves here.
    for n in sorted(expected_exposures.keys()):
        corrected.append(prepare_missing_exposure(n))

    # Ensure they really are sorted.
    return sorted(corrected, key=lambda x: x["exposure"])


def sjd_to_exposure_prefix(sjd: int):
    return (sjd - 55_562) * 10_000


def exposure_prefix_to_sjd(prefix: int):
    return (prefix // 10_000) + 55_562


def get_expected_exposure_metadata(observatory: str, mjd: int) -> Dict[int, Dict]:
    """
    Query the SDSS database to get the expected exposures for a given observatory and MJD.
    This is useful for identifying missing exposures.
    """

    if mjd < getattr(config.sdssdb_exposure_min_mjd, observatory):
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
            (opsdb.Exposure.exposure_no > sjd_to_exposure_prefix(mjd))
            & (opsdb.Exposure.exposure_no < sjd_to_exposure_prefix(mjd + 1))
        )
        .join(
            opsdb.ExposureFlavor,
            on=(opsdb.ExposureFlavor.pk == opsdb.Exposure.exposure_flavor),
        )
        .dicts()
    )
    defaults = dict(observatory=observatory, mjd=mjd)
    return {r["exposure"]: {**defaults, **r} for r in q}


def get_almanac_data(observatory: str, mjd: int, fibers=False, xmatch=False, **kwargs):
    """
    Return a generator of metadata for all exposures taken from a given observatory on a given MJD.
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

    exposures = organize_exposures(exposures_on_disk, expected_exposures)
    logger.debug(f"{observatory}/{mjd} joined: {len(exposures)}")

    if len(exposures) == 0:
        return None

    exposures = Table(rows=list(exposures))

    sequence_indices = {
        "objects": get_object_sequence_indices(exposures),
        "arclamps": get_arclamp_sequence_indices(exposures),
    }

    fiber_maps = dict(fps={}, plates={})
    if fibers:
        configids = set(exposures["configid"]).difference({"", "-1", "-999"})
        plateids = set(exposures["plateid"]).difference(
            {"", "0", "-1"}
        )  # plate ids often 0
        # make sure neither set contains None
        configids.discard(None)
        plateids.discard(None)
        logger.debug(f"{observatory}/{mjd} checking fibers")
        catalogids, fps_fiber_maps = get_fiber_mappings(
            get_fps_targets, configids, observatory
        )
        logger.debug(f"{observatory}/{mjd} has {len(catalogids)} unique catalogids")
        twomass_designations, plate_fiber_maps = get_fiber_mappings(
            get_plate_targets, plateids
        )
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
    return (exposures, sequence_indices, fiber_maps)


def get_sequence_exposure_numbers(
    exposures,
    imagetyp: str,
    keys: Tuple[str],
    require_contiguous: bool = True,
    require_path_exists: bool = True,
):
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


def get_arclamp_sequence_indices(exposures, **kwargs):
    sequence_exposure_numbers = get_sequence_exposure_numbers(
        exposures, imagetyp="ArcLamp", keys=("dithpix",), **kwargs
    )
    sequence_indices = np.searchsorted(exposures["exposure"], sequence_exposure_numbers)
    if sequence_indices.size > 0:
        sequence_indices += [0, 1]  # to offset the end index
    return np.sort(sequence_indices, axis=0)


def get_object_sequence_indices(exposures, **kwargs):
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


def get_unique_exposure_paths(paths):

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
        path = f"{SAS_BASE_DIR}/sdsswork/data/apogee/{observatory}/{mjd}/{prefix}-{chip}-{exposure_apz}"
        unique_exposure_paths.append((path, chips))

    return unique_exposure_paths


def get_fiber_mappings(f, iterable, *args):
    all_ids, mappings = (set(), {})
    for item in iterable:
        ids, mapping = f(item, *args)
        mappings[item] = mapping
        all_ids.update(ids)
    return (all_ids, mappings)
