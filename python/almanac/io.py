
import h5py as h5
import numpy as np
from tqdm import tqdm
from astropy.io.misc.hdf5 import write_table_hdf5

def get_or_create_group(fp, group_name):
    try:
        group = fp[group_name]
    except KeyError:
        group = fp.create_group(group_name)
    finally:
        return group
    
def delete_hdf5_entry(fp, group_name):
    try:
        del fp[group_name]
    except KeyError:
        pass

def _update_almanac(fp, exposures, sequence_indices, fiber_maps, compression=True, verbose=False):

    _print = print if verbose else lambda *args, **kwargs: None
    observatory, mjd = (exposures["observatory"][0], exposures["mjd"][0])
    group = get_or_create_group(fp, f"{observatory}/{mjd}")
    
    delete_hdf5_entry(group, "exposures")
    write_table_hdf5(exposures, group, "exposures", compression=compression)
    
    _print(f"\t{observatory}")
    _print(f"\t{observatory}/{mjd}")
    _print(f"\t{observatory}/{mjd}/exposures")
    
    if len(sequence_indices) > 0:
        delete_hdf5_entry(group, "sequences")
        group.create_dataset(
            "sequences",
            data=np.array(exposures["exposure"][sequence_indices - [0, 1]])
        )
        _print(f"\t{observatory}/{mjd}/sequences")

    for fiber_type, mapping in fiber_maps.items():
        for refid, targets in mapping.items():                
            g = get_or_create_group(group, f"fibers/{fiber_type}")
            delete_hdf5_entry(group, f"fibers/{fiber_type}/{refid}")
            write_table_hdf5(
                targets,
                g,
                refid,
                compression=compression,
            )             
                            
            _print(f"\t{observatory}/{mjd}/fibers/{fiber_type}/{refid}")
        

def write_almanac(output, results, **kwargs):
    
    with h5.File(output, "a") as fp:
        for args in tqdm(results, desc=f"Updating {output}"):
            _update_almanac(fp, *args, **kwargs)
