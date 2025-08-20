#!/usr/bin/env python3

import click

#if ctx.invoked_subcommand is None:
#        ctx.invoke(query, **ctx.params)


@click.group(invoke_without_command=True)
@click.option('-v', '--verbosity', count=True, help="Verbosity level")
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
@click.option('--exposure-columns', default="observatory,mjd,exposure,lampqrtz,lampthar,lampune,fieldid,plateid,cartid,configid,imagetyp,dithpix", help="Comma-separated list of exposure columns to show", show_default=True)
@click.option('--fps-columns', default="sdss_id,catalogid,program,category,firstcarton,ra,dec,fiberId", help="Comma-separated list of fiber positioner columns to show", show_default=True)
@click.option('--plate-columns', default="sdss_id,target_id,target_ra,target_dec,target_type,source_type,fiber_id", help="Comma-separated list of plate columns to show", show_default=True)
@click.pass_context
def main(ctx, verbosity, mjd, mjd_start, mjd_end, date, date_start, date_end, apo, lco, fibers, no_x_match, output, processes, exposure_columns, fps_columns, plate_columns):
    """
    Almanac collects metadata from planned and actual APOGEE exposures,
    and identifies sequences of exposures that constitute epoch visits. 
    """    

    # This keeps the default behaviour as 'query mode' but allows for commands like 'config'.
    if ctx.invoked_subcommand is not None:
        command = dict(
            config=config
        )[ctx.invoked_subcommand]
        return ctx.invoke(command, **ctx.params)

    from tqdm import tqdm
    from itertools import product
    from almanac import (apogee, io, utils)

    tqdm_kwds = dict(disable=(verbosity < 1))

    if output is None and verbosity == 0:
        verbosity = 2
        
    show_exposure_columns = exposure_columns.split(",")
    show_fps_columns = fps_columns.split(",")
    show_plate_columns = plate_columns.split(",")
    
    def pretty_print_progress(exposures, sequence_indices, fiber_maps):
        if verbosity >= 2:
            utils.pretty_print_exposures(
                exposures[show_exposure_columns],
                sequence_indices
            )
        if verbosity >= 3:
            for fiber_type, mapping in fiber_maps.items():
                columns = show_fps_columns if fiber_type == "fps" else show_plate_columns                    
                for refid, targets in mapping.items():
                    if len(targets) > 0:
                        utils.pretty_print_targets(targets[columns], fiber_type, refid)    
    
    
    mjds = utils.parse_mjds(mjd, mjd_start, mjd_end, date, date_start, date_end)
    observatories = utils.get_observatories(apo, lco)
    
    iterable = product(observatories, mjds)    
    results = []
    if processes is not None:
        # Parallel
        import os
        import signal
        import concurrent.futures
        with concurrent.futures.ProcessPoolExecutor(max_workers=processes) as pool:
            futures = []
            for total, (observatory, mjd) in enumerate(iterable, start=1):
                futures.append(pool.submit(apogee.get_almanac_data, observatory, mjd, fibers, not no_x_match))

            with tqdm(desc="Collecting data", total=total, **tqdm_kwds) as pb:
                try:                
                    for future in concurrent.futures.as_completed(futures):
                        pb.update()
                        result = future.result()
                        if result is None: 
                            continue
                        
                        pretty_print_progress(*result)
                        results.append(result)

                except KeyboardInterrupt:
                    for pid in pool._processes:
                        os.kill(pid, signal.SIGKILL)
                    pool.shutdown(wait=False, cancel_futures=True)                
                    raise KeyboardInterrupt
    
    else:
        for observatory, mjd in tqdm(iterable, total=len(mjds) * len(observatories), **tqdm_kwds):
            result = apogee.get_almanac_data(observatory, mjd, fibers, not no_x_match)
            if result is None: continue
            
            pretty_print_progress(*result)
            results.append(result)

    if output:
        io.write_almanac(output, results, verbose=(verbosity >= 3))


@main.group()
def config(**kwargs):
    """View or update configuration settings."""
    pass


@config.command()
def show(**kwargs):
    """Show all configuration settings""" 
    
    from almanac.config import asdict, config, get_config_path
    
    click.echo(f"Configuration path: {get_config_path()}")
    click.echo(f"Configuration:")
    
    def _pretty_print(config_dict, indent=""):
        for k, v in config_dict.items():
            if isinstance(v, dict):
                click.echo(f"{indent}{k}:")
                _pretty_print(v, indent=indent + "  ")
            else:
                click.echo(f"{indent}{k}: {v}")

    _pretty_print(asdict(config), "  ")


@config.command
@click.argument("key", type=str)
def get(key, **kwargs):
    """Get a configuration value"""

    from almanac.config import config, asdict

    def traverse(config, key, provenance=None, sep="."):
        parent, *child = key.split(sep, 1)
        try:
            # TODO: Should we even allow dicts in config?
            if isinstance(config, dict):
                v = config[parent]
            else:
                v = getattr(config, parent)
        except (AttributeError, KeyError):
            context = sep.join(provenance or [])
            if context:
                context = f" within '{context}'"

            if not isinstance(config, dict):
                config = asdict(config)
                        
            raise click.ClickException(
                    f"No configuration key '{parent}'{context}. "
                    f"Available{context}: {', '.join(config.keys())}"
                )

        provenance = (provenance or []) + [parent]
        return traverse(v, child[0], provenance) if child else v


    value = traverse(config, key)
    click.echo(value)

@config.command
@click.argument("key")
@click.argument("value")
def set(key, value, **kwargs):
    """Update a configuration value"""

    from almanac.config import (
        config, asdict, is_dataclass, get_config_path, ConfigManager
    )

    def traverse(config, key, value, provenance=None, sep="."):
        parent, *child = key.split(sep, 1)
        
        try:
            scope = getattr(config, parent)
        except AttributeError:
            context = sep.join(provenance or [])
            if context:
                context = f" within '{context}'"

            if not isinstance(config, dict):
                config = asdict(config)

            raise click.ClickException(
                f"No configuration key '{parent}'{context}. "
                f"Available{context}: {', '.join(config.keys())}"
            )

        else:

            if not child:

                fields = {f.name: f.type for f in config.__dataclass_fields__.values()}
                field_type = fields[parent]
                if is_dataclass(field_type):
                    context = sep.join(provenance or [])
                    if context:
                        context = f" within '{context}'"

                    raise click.ClickException(
                        f"Key '{parent}'{context} refers to a configuration class. "
                        f"You must set the values of the configuration class individually. "
                        f"Sorry! "
                        f"Or you can directly edit the configuration file {get_config_path()}"
                    )
            
                setattr(config, parent, value)
            else:
                provenance = (provenance or []) + [parent]
                traverse(scope, child[0], value)

    traverse(config, key, value)
    config_path = get_config_path()
    ConfigManager.save(config, config_path)
    click.echo(f"Updated configuration {key} to {value} in {config_path}")



if __name__ == '__main__':
    main()
