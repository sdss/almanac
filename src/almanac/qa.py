from astropy.table import Table
from importlib import resources

def get_bad_exposures():
    with resources.as_file(resources.files("almanac.etc") / "bad_exposures.csv") as fp:
        t = Table.read(fp)
        # We want a lookup table for (observatory, mjd, exposure)
        t["exposure"] = t["exposure"].filled(-1)
        d = {}
        for row in t:
            key = (str(row["observatory"]), int(row["mjd"]), int(row["exposure"]))
            try:
                plate = str(row["plate"])
            except:
                plate = -999
            d[key] = {
                "image_type": str(row["image_type"]),
                "plate": plate,
                "notes": str(row["notes"])
            }
        return d


lookup_bad_exposures = get_bad_exposures()
