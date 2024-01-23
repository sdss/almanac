import re
from subprocess import check_output

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
    
def get_headers(path, keys=RAW_HEADER_KEYS, head=100_000):
    keys_str = "|".join(keys) 
    commands = " | ".join([
        'hexdump -n {head} -e \'80/1 "%_p" "\\n"\' {path}',
        'egrep "{keys_str}"'
    ]).format(head=head, path=path, keys_str=keys_str)
    outputs = check_output(commands, shell=True, text=True)
    outputs = outputs.strip().split("\n") 
    values = _parse_hexdump_headers(outputs, keys)
    _, telescope, mjd, basename = path.rsplit("/", 3)
    prefix, chip, exposure = basename.split("-")
    exposure = exposure.strip(".apz")
    return [telescope, mjd, exposure, prefix, chip] + values


def get_plateHole_path(plate_id):
    plate_id = int(plate_id)
    return f"/uufs/chpc.utah.edu/common/home/sdss09/software/svn.sdss.org/data/sdss/platelist/trunk/plates/{str(plate_id)[:-2].zfill(4)}XX/{plate_id:0>6.0f}/plateHoles-{plate_id:0>6.0f}.par"

def get_apogee_plate_targets(plate_id):
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
    
def get_apogee_fps_targets(config_id):
    lkeys = "_, positionerId, holeId, fiberType, assigned, on_target, valid, decollided, xwok, ywok, zwok, xFocal, yFocal, alpha, beta, racat,  deccat, pmra, pmdex, parallax, ra, dec, lambda_eff, coord_epoch, spectrographId, fiberId".split(", ")
    rkeys = "catalogid, carton_to_target_pk, cadence, firstcarton, program, category, sdssv_boss_target0, sdssv_apogee_target0, delta_ra, delta_dec".split(", ")
            
    targets = []
    with open(get_confSummary_path(config_id), "r") as fp:
        for line in fp:
            if line.startswith("FIBERMAP"):
                lvalues = line.split(" ", len(lkeys))[:-1]
                rvalues = line.rsplit(" ", len(rkeys))[1:]
                target = dict(zip(lkeys + rkeys, lvalues + rvalues))
                if target["fiberType"] == "APOGEE":
                    targets.append(target)                 
    return targets




if __name__ == "__main__":

    MAX_WORKERS = 128
    
    from glob import glob
    from tqdm import tqdm
    import concurrent.futures


    telescopes = ("apo", "lco")
    
    folders = []
    for telescope in telescopes:
        folders.extend(glob(f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{telescope}/*"))
    print(f"{len(folders)} telescope/mjd level folders found")
    
    all_paths = []
    for folder in folders:
        all_paths.extend(glob(f"{folder}/a?R-*.apz"))
    
    print(f"{len(all_paths)} a?R-*.apz files found")
    
    # Restrict to one of the three chips for each exposure.
    chip_mapping = {}
    for path in all_paths:
        _, telescope, mjd, basename = path.rsplit("/", 3)
        prefix, chip, exposure = basename.split("-")
        exposure = exposure.strip(".apz")
        
        key = (telescope, mjd, exposure)
        chip_mapping.setdefault(key, [False, False, False])
        index = "abc".index(chip)
        chip_mapping[key][index] = True
    
    print(f"Found {len(chip_mapping)} files to check")
    
    pool = concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS)
    
    futures = []
    for (telescope, mjd, exposure), chips in tqdm(chip_mapping.items(), desc="Creating futures"):
        chip = "abc"[chips.index(True)]
        sp = "p" if telescope == "apo" else "s"
        path = f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{telescope}/{mjd}/a{sp}R-{chip}-{exposure}.apz"
        futures.append(pool.submit(get_headers, path))
    
    results = []
    with tqdm(total=len(futures), desc="Collecting metadata") as pb:        
        for future in concurrent.futures.as_completed(futures):
            telescope, mjd, exposure, prefix, chip, *values = future.result()
            # Check for chips
            has_chip_a, has_chip_b, has_chip_c = chip_mapping[(telescope, mjd, exposure)]            
            results.append(
                [
                    telescope,
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
            
    names = ["telescope", "mjd", "exposure", "prefix", "chip", "has_chip_a", "has_chip_b", "has_chip_c"] + list(map(str.lower, RAW_HEADER_KEYS))

    from astropy.table import Table
    meta = Table(rows=results, names=["path"] + list(map(str.lower, RAW_HEADER_KEYS)))
    
    
        
        
    '''    
    
    # for a MJD, loop over all images and extract the header info
    # -> if it has a CONFIGID, then read the FPS target file
    # -> if it doesn't, use the plateHole file
    import sys
    import os
    from glob import glob
    
    telescope, mjd = sys.argv[1:3]
    
    # Don't load them if we already have them
    FPS_TARGETS = {}
    PLATE_TARGETS = {}
    
    paths = glob(f"/uufs/chpc.utah.edu/common/home/sdss/sdsswork/data/apogee/{telescope}/{mjd}/a?R-*.apz")
    
    for path in paths:
        meta = get_headers(path)
        
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
                    targets = PLATE_TARGETS[plate_id] = get_apogee_plate_targets(plate_id)
        
        else:
            # FPS
            config_id = meta["CONFIGID"]
            try:
                targets = FPS_TARGETS[plate_id]
            except KeyError:
                targets = FPS_TARGETS[plate_id] = get_apogee_fps_targets(config_id)
                
        print(os.path.basename(path), meta, len(targets)) 
        for target in targets:
            print(f"\t>{target}")
            
    
    # meta/telescope/mjd
    # plates/plate_id
    # fps/config_id
    '''
