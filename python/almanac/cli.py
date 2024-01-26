#/usr/bin/python

import click
@click.command()
@click.option('-s', '--silent', is_flag=True, help="Silence output")
@click.option('--mjd', default=None, type=int, help="Modified Julian date to query. Use negative values to indicate relative to current MJD.")
@click.option('--mjd-start', default=None, type=int, help="Start of MJD range to query")
@click.option('--mjd-end', default=None, type=int, help="End of MJD range to query")
@click.option('--date', default=None, type=str, help="Date to query (e.g., 2024-01-15)")
@click.option('--date-start', default=None, type=str, help="Start of date range to query")
@click.option('--date-end', default=None, type=str, help="End of date range to query")
@click.option('--apo', is_flag=True, help="Query Apache Point Observatory data")
@click.option('--lco', is_flag=True, help="Query Las Campanas Observatory data")
@click.option('--fibers', '--fibres', is_flag=True, help="Include fibre mappings to targets")
@click.option('--no-x-match', is_flag=True, help="Do not cross-match targets with SDSS-V database")
@click.option('--output', '-O', default=None, type=str, help="Output file")
@click.option('--processes', '-p', default=None, type=int, help="Number of processes to use")
@click.option('--profile', default="operations", type=str, help="sdssdb database profile")
def main(silent, mjd, mjd_start, mjd_end, date, date_start, date_end, apo, lco, fibers, no_x_match, output, processes, profile):
    """
    The almanac extracts metadata from raw APOGEE exposures (including fiber mappings)
    and finds sequences of exposures that form individual visits.
    """    
    
    from itertools import product
    from astropy.table import Table

    from almanac import utils
    from almanac.apogee import (
        get_exposure_metadata, 
        get_exposure_metadata_as_list, 
        get_sequence_indices,
        get_fps_fiber_maps,
        get_plate_fiber_maps
    )

    tqdm_kwds = dict(disable=silent)
    print_columns = ["observatory", "mjd", "exposure", "chip", "fieldid", "plateid", "cartid", "configid", "imagetyp"]

    mjds = utils.parse_mjds(mjd, mjd_start, mjd_end, date, date_start, date_end)
    observatories = utils.get_observatories(apo, lco)
    
    iterable = product(observatories, mjds)

    exposures_and_sequence_indices = []
    
    if processes is not None:
        # Parallel
        import concurrent.futures
        pool = concurrent.futures.ProcessPoolExecutor(max_workers=processes)
        
        futures = []
        for observatory, mjd in iterable:
            futures.append(pool.submit(get_exposure_metadata_as_list, observatory, mjd))

        for future in concurrent.futures.as_completed(futures):
            rows = future.result()
            if len(rows) == 0: 
                continue
            
            exposures = Table(rows=rows)
            exposures.sort(("exposure", ))
            
            sequence_indices = get_sequence_indices(exposures)
            exposures_and_sequence_indices.append((exposures, sequence_indices))
            if not silent:
                utils.pretty_print_table(
                    exposures[print_columns],
                    sequence_indices
                )    
    else:
        # Serial    
        for observatory, mjd in product(observatories, mjds):
            rows = list(get_exposure_metadata(observatory, mjd))
            if len(rows) == 0: 
                continue
            
            exposures = Table(rows=rows)
            exposures.sort(("exposure", ))
            
            sequence_indices = get_sequence_indices(exposures)            
            exposures_and_sequence_indices.append((exposures, sequence_indices))
            if not silent:
                utils.pretty_print_table(
                    exposures[print_columns], 
                    sequence_indices
                )
    
    fps_fiber_maps, plate_fiber_maps = ({}, {})
    
    if fibers:
        # Get unique configurations (plate and FPS)
        configids, plateids = (set(), set())
        for exposures, sequence_indices in exposures_and_sequence_indices:
            configids.update(exposures["configid"])
            plateids.update(exposures["plateid"])    
        
        plateids.discard("")
        configids.discard("")
        
        if plateids or configids:            
            try:
                from sdssdb.peewee.sdss5db import catalogdb
            except ImportError:
                click.echo("Could not import `sdssdb`: have you run `module load sdssdb`?", err=True)                
            else:            
                catalogdb.database.set_profile(profile)        
                fps_fiber_maps.update(get_fps_fiber_maps(configids, no_x_match=no_x_match, tqdm_kwds=tqdm_kwds))
                plate_fiber_maps.update(get_plate_fiber_maps(plateids, no_x_match=no_x_match, tqdm_kwds=tqdm_kwds))
        
    # Write the output to disk
    if output:
        from almanac.io import write_almanac 
        write_almanac(output, exposures_and_sequence_indices, fps_fiber_maps, plate_fiber_maps, verbose=(not silent))


if __name__ == '__main__':
    main()
