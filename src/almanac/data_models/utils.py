import numpy as np
from astropy.table import Table, hstack
from scipy.spatial.distance import cdist
from subprocess import check_output
from typing import List, Tuple

from almanac import utils
from almanac.config import config
from almanac.logger import logger

def match_planned_to_plugged(plate_hole_path, plug_map_path, tol=1e-5):

    planned = Table.read(plate_hole_path, format="yanny", tablename="STRUCT1")
    plugged = Table.read(plug_map_path, format="yanny", tablename="PLUGMAPOBJ")

    planned = planned[
        (planned["holetype"] == "APOGEE")
    |   (planned["holetype"] == "APOGEE_SHARED")
    |   (planned["holetype"] == "APOGEE_SOUTH")
    ]
    plugged = plugged[plugged["spectrographId"] == 2]

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

    N = np.sum(n_matches_to_plugged_holes > 1)
    if N > 0:
        logger.warning(
            f"{N} plugged holes match multiple planned holes!\n"
            f"\tPlanned holes: {plate_hole_path}\n"
            f"\tPlugged holes: {plug_map_path}\n"
        )
        logger.warning(f"Following indices are all 1-indexed.")
        for plugged_index in np.where(n_matches_to_plugged_holes > 1)[0]:
            n = n_matches_to_plugged_holes[plugged_index]
            logger.warning(
                f"Plugged hole index {plugged_index + 1} "
                f"(ra={plugged['ra'][plugged_index]:.5f}, dec={plugged['dec'][plugged_index]:.5f}) "
                f"matches {n} planned holes within {tol:.1e}:"
            )
            for i, planned_index in enumerate(np.where(meets_tolerance[:, plugged_index])[0], start=1):
                logger.warning(
                    f"\t {i}. Planned hole index {planned_index + 1} matches coordinates (ra={planned['target_ra'][planned_index]:.5f}, dec={planned['target_dec'][planned_index]:.5f})"
                )

        raise RuntimeError("Cannot uniquely match plugged holes to planned holes!")

    dist = np.sqrt(ra_dist**2 + dec_dist**2)
    has_match = (n_matches_to_plugged_holes == 1)
    planned_hole_indices = np.argmin(dist[:, has_match], axis=0)

    return hstack(
        [
            plugged[has_match],
            planned[planned_hole_indices]
        ],
        metadata_conflicts="silent",
        uniq_col_name="{table_name}{col_name}",
        table_names=("", "planned_")
    )


def get_headers(path, head=20_000):
    keys = (
        "FIELDID", "DESIGNID", "CONFIGID", "SEEING", "EXPTYPE",
        "NREAD", "IMAGETYP", "LAMPQRTZ", "LAMPTHAR", "LAMPUNE", "FOCUS",
        "NAME", "PLATEID", "CARTID", "MAPID", "PLATETYP", "OBSCMNT",
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


def get_exposure_path(observatory, mjd, prefix, exposure, chip):
    return (
        f"{config.apogee_dir}/"
        f"{observatory}/"
        f"{mjd}/"
        f"{prefix}-{chip}-{get_exposure_string(mjd, exposure)}.apz"
    )

def mjd_to_exposure_prefix(mjd: int) -> int:
    """Convert MJD to exposure prefix.

    The exposure prefix is calculated as (MJD - 55562) * 10000, with a minimum of 0.

    :param mjd:
        Modified Julian Date (MJD) as an integer.

    :returns:
        Exposure prefix as an integer.
    """
    return max(0, (int(mjd) - 55_562) * 10_000)


def get_exposure_string(mjd, exposure):
    if isinstance(exposure, str):
        return exposure
    else:
        return f"{mjd_to_exposure_prefix(mjd) + exposure:08d}"



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
