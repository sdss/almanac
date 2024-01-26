
import h5py as h5
import numpy as np
from astropy.table import Table
from astropy.io.misc.hdf5 import write_table_hdf5

def write_almanac(output_path, exposures_and_sequence_indices, fps_fiber_maps=None, plate_fiber_maps=None, compression=True, mode="a", verbose=False):
    
    
    """
    Structure:
    
    {observatory}/{mjd}/exposures
    {observatory}/{mjd}/sequences -> (start, end) of exposure numbers (inclusive)
    {observatory}/{mjd}/fibers/fps/{config_id}
    {observatory}/{mjd}/fibers/plates/{plateid}
    """
    
    _print = print if verbose else lambda *args, **kwargs: None

    fps_fiber_maps = fps_fiber_maps or {}
    plate_fiber_maps = plate_fiber_maps or {}
    
    any_fiber_maps = (len(fps_fiber_maps) > 0) or (len(plate_fiber_maps) > 0)
        
    with h5.File(output_path, mode) as fp:
        
        _print(f"Writing to output file {output_path}:")
        for exposures, sequence_indices in exposures_and_sequence_indices:
            
            observatory, mjd = (exposures["observatory"][0], exposures["mjd"][0])
            group_name = f"{observatory}/{mjd}"
            group = fp[group_name] if group_name in fp else fp.create_group(group_name)
            
            _print(f"\t{group_name}")
                
            if "exposures" in group:
                del group["exposures"]
            write_table_hdf5(exposures, group, "exposures", compression=compression)
            _print(f"\t{group_name}/exposures")
    
            if len(sequence_indices) > 0:
                if "sequences" in group:
                    del group["sequences"]
                group.create_dataset(
                    "sequences",
                    data=np.array(exposures["exposure"][sequence_indices - [0, 1]])
                )
                _print(f"\t{group_name}/sequences")
            
            if any_fiber_maps:
                # for this mjd
                gnf = "fibers"
                fibers_group = group[gnf] if gnf in group else group.create_group(gnf)
                _print(f"\t{group_name}/{gnf}")
                
                configids = set(exposures["configid"]).difference({""})
                plateids = set(exposures["plateid"]).difference({""})
                
                if configids:
                    gn = "fps"
                    fps_group = fibers_group[gn] if gn in fibers_group else fibers_group.create_group(gn)
                    _print(f"\t{group_name}/{gnf}/{gn}")
                    
                    for config_id in map(str, sorted(tuple(map(int, configids)))):
                        if config_id in fps_group:
                            del fps_group[config_id]
                        write_table_hdf5(
                            Table(rows=fps_fiber_maps[config_id]),
                            fps_group,
                            config_id,
                            compression=compression,
                        )
                        _print(f"\t{group_name}/{gnf}/fps/{config_id}")
                
                if plateids:
                    gn = "plates"
                    plates_group = fibers_group[gn] if gn in fibers_group else fibers_group.create_group(gn)                    
                    _print(f"\t{group_name}/{gnf}/{gn}")                    
                    for plateid in map(str, sorted(tuple(map(int, plateids)))):
                        if plateid in plates_group:
                            del plates_group[plateid]
                        write_table_hdf5(
                            Table(rows=plate_fiber_maps[plateid]),
                            plates_group,
                            plateid,
                            compression=compression,
                        )
                        _print(f"\t{group_name}/{gnf}/{gn}/{plateid}")
