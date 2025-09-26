#!/usr/bin/env python3

import click


@click.group(invoke_without_command=True)
@click.option("-v", "--verbosity", count=True, help="Verbosity level")
@click.option("--mjd", default=None, type=int, help="Modified Julian date to query. Use negative values to indicate relative to current MJD")
@click.option("--mjd-start", default=None, type=int, help="Start of MJD range to query")
@click.option("--mjd-end", default=None, type=int, help="End of MJD range to query")
@click.option("--date", default=None, type=str, help="Date to query (e.g., 2024-01-15)")
@click.option("--date-start", default=None, type=str, help="Start of date range to query")
@click.option("--date-end", default=None, type=str, help="End of date range to query")
@click.option("--apo", is_flag=True, help="Query Apache Point Observatory data")
@click.option("--lco", is_flag=True, help="Query Las Campanas Observatory data")
@click.option("--fibers", "--fibres", is_flag=True, help="Include fibre mappings to targets")
@click.option("--no-x-match", is_flag=True, help="Do not cross-match targets with SDSS-V database")
@click.option("--output", "-O", default=None, type=str, help="Output file")
@click.option("--processes", "-p", default=None, type=int, help="Number of processes to use")
@click.pass_context
def main(
    ctx,
    verbosity,
    mjd,
    mjd_start,
    mjd_end,
    date,
    date_start,
    date_end,
    apo,
    lco,
    fibers,
    no_x_match,
    output,
    processes,
):
    """
    Almanac collects metadata from planned and actual APOGEE exposures,
    and identifies sequences of exposures that constitute epoch visits.
    """

    # This keeps the default behaviour as 'query mode' but allows for commands like 'config'.
    if ctx.invoked_subcommand is not None:
        command = dict(config=config, dump=dump)[ctx.invoked_subcommand]
        return ctx.invoke(command, **ctx.params)

    import h5py as h5
    from itertools import product
    from rich.live import Live
    from almanac.display import ObservationsDisplay
    from almanac import apogee, logger, io, utils
    from contextlib import nullcontext
    from time import time, sleep

    mjds, mjd_min, mjd_max = utils.parse_mjds(mjd, mjd_start, mjd_end, date, date_start, date_end)
    observatories = utils.get_observatories(apo, lco)

    n_iterables = len(mjds) * len(observatories)
    iterable = product(mjds, observatories)
    results = []

    display = ObservationsDisplay(mjd_min, mjd_max, observatories)

    buffered_critical_logs = []
    buffered_result_rows = []

    refresh_per_second = 1
    context_manager = (
        Live(
            display.create_display(),
            refresh_per_second=refresh_per_second,
            screen=True
        )
        if verbosity >= 1
        else nullcontext()
    )
    io_kwds = dict(fibers=fibers, compression=False)
    with (h5.File(output, "a") if output else nullcontext()) as fp:
        with context_manager as live:
            if processes is not None:
                def initializer():
                    from sdssdb.peewee.sdss5db import database

                    if hasattr(database, "_state"):
                        database._state.closed = True
                        database._state.conn = None
                    from almanac.database import database

                # Parallel
                import os
                import signal
                import concurrent.futures
                if processes < 0:
                    processes = os.cpu_count()
                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=processes, initializer=initializer
                ) as pool:

                    try:
                        futures = set()
                        for n, (mjd, observatory) in enumerate(iterable, start=1):
                            futures.add(
                                pool.submit(
                                    apogee.get_almanac_data,
                                    observatory,
                                    mjd,
                                    fibers,
                                    not no_x_match,
                                )
                            )
                            if n == processes:
                                break

                        t = time()
                        while len(futures) > 0:

                            future = next(concurrent.futures.as_completed(futures))

                            observatory, mjd, exposures, sequences = future.result()

                            v = mjd - mjd_min + display.offset
                            missing = [e.image_type == "missing" for e in exposures]
                            if any(missing):
                                display.missing.add(v)
                                #buffered_critical_logs.extend(missing)

                            if not exposures:
                                display.no_data[observatory].add(v)
                            else:
                                display.completed[observatory].add(v)
                                if output:
                                    io.update(fp, observatory, mjd, exposures, sequences, **io_kwds)

                            if live is not None and (time() - t) > 1 / refresh_per_second:
                                live.update(display.create_display())
                                t = time()
                            futures.remove(future)

                            try:
                                mjd, observatory = next(iterable)
                            except StopIteration:
                                None
                            else:
                                futures.add(
                                    pool.submit(
                                        apogee.get_almanac_data,
                                        observatory,
                                        mjd,
                                        fibers,
                                        not no_x_match,
                                    )
                                )


                    except KeyboardInterrupt:
                        for pid in pool._processes:
                            os.kill(pid, signal.SIGKILL)
                        pool.shutdown(wait=False, cancel_futures=True)
                        try:
                            fp.close()
                        except:
                            None
                        raise KeyboardInterrupt
            else:
                t = time()
                for mjd, observatory in iterable:
                    *_, exposures, sequences = apogee.get_almanac_data(observatory, mjd, fibers, not no_x_match)
                    v = mjd - mjd_min + display.offset
                    if any([e.image_type == "missing" for e in exposures]):
                        display.missing.add(v)
                        #buffered_critical_logs.extend(missing)

                    if not exposures:
                        display.no_data[observatory].add(v)
                    else:
                        display.completed[observatory].add(v)
                        if output:
                            io.update(fp, observatory, mjd, exposures, sequences, **io_kwds)

                    if live is not None and (time() - t) > 1 / refresh_per_second:
                        live.update(display.create_display())
                        t = time()

            if live is not None:
                live.update(display.create_display())
                sleep(3)

    #if verbosity >= 2:
    #    from almanac.utils import rich_display_exposures
    #    for e, s, *_ in results:
    #        rich_display_exposures(e, s, column_names=show_exposure_columns)

    # Show critical logs at the end to avoid disrupting the display
        for item in buffered_critical_logs:
            logger.critical(item)

    """
    if output:
        io.write_almanac(
            output,
            results,
            fibers=fibers,
            verbose=(verbosity >= 3)
        )
    """

@main.group()
def config(**kwargs):
    """View or update configuration settings."""
    pass


@config.command()
def show(**kwargs):
    """Show all configuration settings"""

    from almanac import config, get_config_path
    from dataclasses import asdict

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

    from almanac import config
    from dataclasses import asdict

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
def update(key, value, **kwargs):
    """Update a configuration value"""

    from almanac import config, get_config_path, ConfigManager
    from dataclasses import asdict, is_dataclass

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


@main.group()
def dump(**kwargs):
    """Dump data to a summary file"""
    pass

# almanac dump star[s] almanac.h5 output.fits


@dump.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file")
def stars(input_path, output_path, overwrite, **kwargs):
    """Create a star-level summary file"""
    pass

@dump.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file")
def visits(input_path, output_path, overwrite,**kwargs):
    """Create a visit-level summary file"""
    pass

@dump.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file")
def exposures(input_path, output_path, overwrite, **kwargs):
    """Create an exposure-level summary file"""

    import h5py as h5
    import numpy as np
    with h5.File(input_path, "r") as fp:
        groups = None
        for observatory in ("apo", "lco"):
            for mjd in fp[observatory].keys():
                group = fp[f"{observatory}/{mjd}/exposures"][:]
                if groups is None:
                    groups = group
                else:
                    groups = np.vstack([groups, group])

        raise a

if __name__ == "__main__":
    main()
