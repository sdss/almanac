import re
import os
import numpy as np
from glob import glob
from subprocess import check_output
from itertools import starmap
from tqdm import tqdm
from astropy.table import Table


SAS_BASE_DIR = os.environ.get("SAS_BASE_DIR", "/uufs/chpc.utah.edu/common/home/sdss/")
PLATELIST_DIR = os.environ.get("PLATELIST_DIR", "/uufs/chpc.utah.edu/common/home/sdss09/software/svn.sdss.org/data/sdss/platelist/trunk/")
SDSSCORE_DIR = os.environ.get("SDSSCORE_DIR", "/uufs/chpc.utah.edu/common/home/sdss50/software/git/sdss/sdsscore/main/")

YANNY_TARGET_MATCH = re.compile(
    'STRUCT1 APOGEE_?\w* (?P<target_type>\w+) (?P<source_type>[\w-]+) (?P<target_ra>[\-\+\.\w\d+]+) (?P<target_dec>[\-\+\.\w\d+]+) \d+ \d+ \d+ (?P<fiber_id>\d+) .+ (?P<target_id>"?[\w\d\s\.\-\+]{1,29}"?) [\d ]?(?P<xfocal>[\-\+\.\w\d+]+) (?P<yfocal>[\-\+\.\w\d+]+)$'
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
    
def _get_meta(path, has_chips=(None, None, None), keys=RAW_HEADER_KEYS, head=20_000):
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
    return (target_id[5:] if target_id.startswith("2MASS") else target_id).lstrip("-Jdb_")


def get_plateHole_path(plate_id):
    plate_id = int(plate_id)
    return f"{PLATELIST_DIR}/plates/{str(plate_id)[:-2].zfill(4)}XX/{plate_id:0>6.0f}/plateHoles-{plate_id:0>6.0f}.par"

def get_plate_targets(plate_id):
    targets, count = ([], 0)
    with open(get_plateHole_path(plate_id), "r") as fp:
        for line in fp:
            if line.startswith("STRUCT1 APOGEE"):
                target = re.match(YANNY_TARGET_MATCH, line).groupdict()
                target["target_id"] = target["target_id"].strip(' "')
                targets.append(target)  
                count += 1
                if count == 500:
                    break
                
                
    return targets

# get FPS plug info
def get_confSummary_path(observatory, config_id):
    return f"{SDSSCORE_DIR}/{observatory}/summary_files/{str(config_id)[:-2].zfill(4)}XX/confSummary-{config_id}.par"
    
def get_fps_targets(observatory, config_id):
    lkeys = "_, positionerId, holeId, fiberType, assigned, on_target, valid, decollided, xwok, ywok, zwok, xFocal, yFocal, alpha, beta, racat,  deccat, pmra, pmdex, parallax, ra, dec, lambda_eff, coord_epoch, spectrographId, fiberId".split(", ")
    rkeys = "catalogid, carton_to_target_pk, cadence, firstcarton, program, category, sdssv_boss_target0, sdssv_apogee_target0, delta_ra, delta_dec".split(", ")
            
    targets = []
    with open(get_confSummary_path(observatory, config_id), "r") as fp:
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
    
    paths = glob(f"{SAS_BASE_DIR}/sdsswork/data/apogee/{observatory}/{mjd}/a?R-*.apz")
    yield from starmap(_get_meta, get_unique_exposure_paths(paths))


def get_almanac_data(observatory: str, mjd: int, fibers=False, xmatch=True, profile="operations", **kwargs):
    """
    Return a generator of metadata for all exposures taken from a given observatory on a given MJD.
    """

    exposures = get_exposure_metadata(observatory, mjd, **kwargs)
            
    exposures = Table(rows=list(exposures))
    if len(exposures) == 0: 
        return None
    exposures.sort(("exposure", ))
    
    sequence_indices = get_sequence_indices(exposures)
    
    fiber_maps = dict(fps={}, plates={})
    if fibers:
        configids = set(exposures["configid"]).difference({"", "-1", "-999"})
        plateids = set(exposures["plateid"]).difference({"", "0", "-1"}) # plate ids often 0
        
        if (plateids or configids) and xmatch:
            try:
                from sdssdb.peewee.sdss5db import catalogdb
            except ImportError:
                # TODO use warnings instead
                print("Could not import `sdssdb`: have you run `module load sdssdb`?")                
                xmatch = False
            else:            
                if not catalogdb.database.set_profile(profile):
                    print(f"Could not connect to SDSS database (profile={profile}). Do you have the necessary entries in your `~/.pgpass` file?")
                    xmatch = False
        
        fiber_maps["fps"].update(get_fps_fiber_maps(observatory, configids, **kwargs))
        fiber_maps["plates"].update(get_plate_fiber_maps(plateids, **kwargs))
    
    for fiber_type, mappings in fiber_maps.items():
        for refid, targets in mappings.items():
            fiber_maps[fiber_type][refid] = Table(rows=targets)
    return (exposures, sequence_indices, fiber_maps)


def get_sequence_exposure_numbers(exposures, keys=("fieldid", "plateid", "configid", "imagetyp")):
    assert len(set(exposures["mjd"])) == 1
    assert len(set(exposures["observatory"])) == 1

    exposures.sort(("exposure", ))
    
    exposure_numbers = []    
    exposures = exposures.group_by(keys)
    for si, ei in zip(exposures.groups.indices[:-1], exposures.groups.indices[1:]):
        if exposures["imagetyp"][si] != "Object":
            continue
        
        # require contiguous exposure numbers
        sub_indices = np.hstack([
            si,
            si + (np.where(np.diff(exposures["exposure"][si:ei]) > 1)[0] + 1),
            ei,
        ])
        for sj, ej in zip(sub_indices[:-1], sub_indices[1:]):        
            exposure_numbers.append(tuple(exposures["exposure"][sj:ej][[0, -1]]))

    return exposure_numbers        


def get_sequence_indices(exposures, **kwargs):
    sequence_exposure_numbers = get_sequence_exposure_numbers(exposures, **kwargs)
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
        path = f"{SAS_BASE_DIR}/sdsswork/data/apogee/{observatory}/{mjd}/{prefix}-{chip}-{exposure_apz}"
        unique_exposure_paths.append((path, chips))

    return unique_exposure_paths

    
def get_fps_fiber_maps(observatory, config_ids, xmatch=True):
    fps_fiber_maps = {}
    if not config_ids:
        return fps_fiber_maps
    
    from sdssdb.peewee.sdss5db import catalogdb
    
    # All FPS targets will have a catalogid, so we will xmatch to database with that (if we need)
    for config_id in config_ids:
        try:
            targets = get_fps_targets(observatory, config_id)
        except:
            targets = []
            print("\tCould not get FPS targets for config_id", config_id)

        if xmatch and len(targets) > 0:
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
                sdss_id_lookup[str(catalogid)] = sdss_id
            
            for target in targets:
                target["sdss_id"] = sdss_id_lookup.get(target["catalogid"], -1)
        else:
            for target in targets:
                target["sdss_id"] = -1
                          
        fps_fiber_maps[config_id] = targets
    return fps_fiber_maps


def get_plate_fiber_maps(plate_ids, xmatch=True):

    plate_fiber_maps = {}
    if not plate_ids:
        return plate_fiber_maps
        
    from sdssdb.peewee.sdss5db import catalogdb

    for plate_id in plate_ids:
        try:
            targets = get_plate_targets(plate_id)
        except:
            targets = []
            print("\tCould not get plate targets for plate_id", plate_id)
            
        if xmatch and len(targets) > 0:
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
        else:
            for target in targets:
                target["sdss_id"] = -1                
        plate_fiber_maps[plate_id] = targets
    
    return plate_fiber_maps
