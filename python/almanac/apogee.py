import re
import numpy as np
from glob import glob
from subprocess import check_output
from itertools import starmap
from tqdm import tqdm

YANNY_TARGET_MATCH = re.compile(
    'STRUCT1 APOGEE (?P<target_type>\w+) (?P<source_type>[\w-]+) (?P<target_ra>\d+\.\d+) (?P<target_dec>\d+\.\d+) \d+ \d+ \d+ (?P<fibre_id>\d+) .+ (?P<target_id>"?[\w\d\s\-\+]{1,25}"?) \d (?P<xfocal>-?\d+\.\d+) (?P<yfocal>-?\d+\.\d+)$'
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
        except ValueError: # grep'd something in the data
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
    
def _get_meta(path, has_chips=(None, None, None), keys=RAW_HEADER_KEYS, head=100_000):
    keys_str = "|".join(keys) 
    commands = " | ".join([
        'hexdump -n {head} -e \'80/1 "%_p" "\\n"\' {path}',
        'egrep "{keys_str}"'
    ]).format(head=head, path=path, keys_str=keys_str)
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
    )
    for prefix, has_chip in zip("abc", has_chips):
        headers[f"readout_chip_{prefix}"] = has_chip
    
    headers.update(dict(zip(map(str.lower, RAW_HEADER_KEYS), values)))
    return headers

def target_id_to_designation(target_id):    
    # The target_ids seem to be styled '2MASS-J...'
    target_id = target_id.strip()
    return (target_id[5:] if target_id.startswith("2MASS") else target_id).lstrip("-J")


def get_plateHole_path(plate_id):
    plate_id = int(plate_id)
    return f"/uufs/chpc.utah.edu/common/home/sdss09/software/svn.sdss.org/data/sdss/platelist/trunk/plates/{str(plate_id)[:-2].zfill(4)}XX/{plate_id:0>6.0f}/plateHoles-{plate_id:0>6.0f}.par"

def get_plate_targets(plate_id):
    targets = []
    with open(get_plateHole_path(plate_id), "r") as fp:
        for line in fp:
            if line.startswith("STRUCT1 APOGEE"):
                target = re.match(YANNY_TARGET_MATCH, line).groupdict()
                target["target_id"] = target["target_id"].strip(' "')
                targets.append(target)    
    return targets

# get FPS plug info
def get_confSummary_path(config_id):
    return f"/uufs/chpc.utah.edu/common/home/sdss50/software/git/sdss/sdsscore/main/apo/summary_files/{str(config_id)[:-2].zfill(4)}XX/confSummary-{config_id}.par"
    
def get_fps_targets(config_id):
    lkeys = "_, positionerId, holeId, fiberType, assigned, on_target, valid, decollided, xwok, ywok, zwok, xFocal, yFocal, alpha, beta, racat,  deccat, pmra, pmdex, parallax, ra, dec, lambda_eff, coord_epoch, spectrographId, fiberId".split(", ")
    rkeys = "catalogid, carton_to_target_pk, cadence, firstcarton, program, category, sdssv_boss_target0, sdssv_apogee_target0, delta_ra, delta_dec".split(", ")
            
    targets = []
    with open(get_confSummary_path(config_id), "r") as fp:
        for line in fp:
            if line.startswith("FIBERMAP"):
                lvalues = line.split(" ", len(lkeys))[:-1]
                rvalues = line.strip().rsplit(" ", len(rkeys))[1:]
                target = dict(zip(lkeys + rkeys, lvalues + rvalues))
                if target["fiberType"] == "APOGEE":
                    targets.append(target)                 
    return targets



def get_exposure_metadata(observatory: str, mjd: int, **kwargs):
    """
    Return a generator of metadata for all exposures taken from a given observatory on a given MJD.
    """
    
    paths = glob(f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{observatory}/{mjd}/a?R-*.apz")
    yield from starmap(_get_meta, get_unique_exposure_paths(paths))


def get_exposure_metadata_as_list(observatory: str, mjd: int, **kwargs):
    return list(get_exposure_metadata(observatory, mjd, **kwargs))


def get_sequence_exposure_numbers(exposures, keys=("fieldid", "plateid", "configid")):
    assert len(set(exposures["mjd"])) == 1
    assert len(set(exposures["observatory"])) == 1

    exposures.sort(("exposure", ))
    
    exposure_numbers = []    
    is_object = (exposures["imagetyp"] == "Object")
    if np.any(is_object):        
        objects = exposures[is_object].group_by(keys)
        for si, ei in zip(objects.groups.indices[:-1], objects.groups.indices[1:]):
            exposure_numbers.append(tuple(objects["exposure"][si:ei][[0, -1]]))

    return exposure_numbers        


def get_sequence_indices(exposures, keys=("fieldid", "plateid", "configid")):
    sequence_exposure_numbers = get_sequence_exposure_numbers(exposures, keys)
    sequence_indices = np.searchsorted(exposures["exposure"], sequence_exposure_numbers)
    if sequence_indices.size > 0:
        sequence_indices += [0, 1] # to offset the end index
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
        path = f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{observatory}/{mjd}/{prefix}-{chip}-{exposure_apz}"
        unique_exposure_paths.append((path, chips))

    return unique_exposure_paths

    
def get_fps_fiber_maps(config_ids, no_x_match=False, tqdm_kwds=None):
    fps_fiber_maps = {}
    if not config_ids:
        return fps_fiber_maps
    
    from sdssdb.peewee.sdss5db import catalogdb
    
    tqdm_kwds = tqdm_kwds or {}
    # All FPS targets will have a catalogid, so we will xmatch to database with that (if we need)
    for config_id in tqdm(config_ids, unit=" configs", desc="Getting fiber maps for FPS", **tqdm_kwds):
        try:
            targets = get_fps_targets(config_id)
        except:
            targets = []
            print("\tCould not get FPS targets for config_id", config_id)

        if not no_x_match and len(targets) > 0:
            # cross-match to the SDSS database
            catalogids = set([target["catalogid"] for target in targets])
            
            q = (
                catalogdb.SDSS_ID_flat
                .select(
                    catalogdb.SDSS_ID_flat.sdss_id,
                    catalogdb.SDSS_ID_flat.catalogid
                )
                .where(catalogdb.SDSS_ID_flat.catalogid.in_(tuple(catalogids)))
                .tuples()
            )
            sdss_id_lookup = {}
            for sdss_id, catalogid in q:
                sdss_id_lookup[catalogid] = sdss_id
            
            for target in targets:
                target["sdss_id"] = sdss_id_lookup.get(target["catalogid"], -1)
                    
        fps_fiber_maps[config_id] = targets
    return fps_fiber_maps


def get_plate_fiber_maps(plate_ids, no_x_match=False, tqdm_kwds=None):

    plate_fiber_maps = {}
    if not plate_ids:
        return plate_fiber_maps
        
    from sdssdb.peewee.sdss5db import catalogdb

    for plate_id in tqdm(plate_ids, unit=" plates", desc="Getting fiber maps for plates", **tqdm_kwds):
        try:
            targets = get_plate_targets(plate_id)
        except:
            targets = []
            print("\tCould not get plate targets for plate_id", plate_id)
            
        if not no_x_match and len(targets) > 0:
            # cross-match to the SDSS database            
            designations = set(tuple(map(target_id_to_designation, (target["target_id"] for target in targets))))
            
            q = (
                catalogdb.SDSS_ID_flat
                .select(
                    catalogdb.SDSS_ID_flat.sdss_id,
                    catalogdb.TwoMassPSC.designation
                )
                .join(catalogdb.CatalogToTwoMassPSC, on=(catalogdb.SDSS_ID_flat.catalogid == catalogdb.CatalogToTwoMassPSC.catalogid))
                .join(catalogdb.TwoMassPSC, on=(catalogdb.CatalogToTwoMassPSC.target_id == catalogdb.TwoMassPSC.pts_key))
                .where(catalogdb.TwoMassPSC.designation.in_(tuple(designations)))
                .tuples()                    
            )
            
            sdss_id_lookup = {}
            for sdss_id, designation in q:
                sdss_id_lookup[designation] = sdss_id
            
            for target in targets:                    
                target["sdss_id"] = sdss_id_lookup.get(target_id_to_designation(target["target_id"]), -1)
                                
        plate_fiber_maps[plate_id] = targets
    
    return plate_fiber_maps


if __name__ == "__main__":

    MAX_WORKERS = 128
    
    from glob import glob
    from tqdm import tqdm
    import concurrent.futures


    observatorys = ("apo", "lco")
    
    folders = []
    for observatory in observatorys:
        folders.extend(glob(f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{observatory}/*"))
    print(f"{len(folders)} observatory/mjd level folders found")
    
    all_paths = []
    for folder in folders:
        all_paths.extend(glob(f"{folder}/a?R-*.apz"))
    
    print(f"{len(all_paths)} a?R-*.apz files found")
    
    # Restrict to one of the three chips for each exposure.
    chip_mapping = {}
    for path in all_paths:
        _, observatory, mjd, basename = path.rsplit("/", 3)
        prefix, chip, exposure = basename.split("-")
        exposure = exposure.strip(".apz")
        
        key = (observatory, mjd, exposure)
        chip_mapping.setdefault(key, [False, False, False])
        index = "abc".index(chip)
        chip_mapping[key][index] = True
    
    print(f"Found {len(chip_mapping)} files to check")
    
    pool = concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS)
    
    futures = []
    for (observatory, mjd, exposure), chips in tqdm(chip_mapping.items(), desc="Creating futures"):
        chip = "abc"[chips.index(True)]
        sp = "p" if observatory == "apo" else "s"
        path = f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{observatory}/{mjd}/a{sp}R-{chip}-{exposure}.apz"
        futures.append(pool.submit(_get_meta, path))
    
    results = []
    with tqdm(total=len(futures), desc="Collecting metadata") as pb:        
        for future in concurrent.futures.as_completed(futures):
            observatory, mjd, exposure, prefix, chip, *values = future.result()
            # Check for chips
            has_chip_a, has_chip_b, has_chip_c = chip_mapping[(observatory, mjd, exposure)]            
            results.append(
                [
                    observatory,
                    mjd,
                    exposure,
                    prefix,
                    chip,
                    has_chip_a,
                    has_chip_b,
                    has_chip_c
                ] + values
            )
            pb.update()
            
    names = ["observatory", "mjd", "exposure", "prefix", "chip", "has_chip_a", "has_chip_b", "has_chip_c"] + list(map(str.lower, RAW_HEADER_KEYS))

    from astropy.table import Table
    meta = Table(rows=results, names=["path"] + list(map(str.lower, RAW_HEADER_KEYS)))
    
    
        
        
    '''    
    
    # for a MJD, loop over all images and extract the header info
    # -> if it has a CONFIGID, then read the FPS target file
    # -> if it doesn't, use the plateHole file
    import sys
    import os
    from glob import glob
    
    observatory, mjd = sys.argv[1:3]
    
    # Don't load them if we already have them
    FPS_TARGETS = {}
    PLATE_TARGETS = {}
    
    paths = glob(f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{observatory}/{mjd}/a?R-*.apz")
    
    for path in paths:
        meta = _get_meta(path)
        
        if meta["CONFIGID"] is None:
            # Assume plates
            plate_id = meta["PLATEID"]
            if plate_id == "0":
                # No plate file!
                targets = []
            else:                
                try:
                    targets = PLATE_TARGETS[plate_id]
                except KeyError:
                    targets = PLATE_TARGETS[plate_id] = get_plate_targets(plate_id)
        
        else:
            # FPS
            config_id = meta["CONFIGID"]
            try:
                targets = FPS_TARGETS[plate_id]
            except KeyError:
                targets = FPS_TARGETS[plate_id] = get_fps_targets(config_id)
                
        print(os.path.basename(path), meta, len(targets)) 
        for target in targets:
            print(f"\t>{target}")
            
    
    # meta/observatory/mjd
    # plates/plate_id
    # fps/config_id
    '''

