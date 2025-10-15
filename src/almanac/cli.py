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
        command = dict(
            config=config,
            dump=dump,
            add=add,
            lookup=lookup
        )[ctx.invoked_subcommand]
        return ctx.invoke(command, **ctx.params)

    import h5py as h5
    from itertools import product
    from rich.live import Live
    from almanac.display import ObservationsDisplay, display_exposures
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

                            observatory, mjd, exposures, sequences = result = future.result()

                            v = mjd - mjd_min + display.offset
                            missing = [e.image_type == "missing" for e in exposures]
                            if any(missing):
                                display.missing.add(v)
                                #buffered_critical_logs.extend(missing)

                            if not exposures:
                                display.no_data[observatory].add(v)
                            else:
                                display.completed[observatory].add(v)
                                results.append(result)
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
                    *_, exposures, sequences = result = apogee.get_almanac_data(observatory, mjd, fibers, not no_x_match)
                    v = mjd - mjd_min + display.offset
                    if any([e.image_type == "missing" for e in exposures]):
                        display.missing.add(v)
                        #buffered_critical_logs.extend(missing)

                    if not exposures:
                        display.no_data[observatory].add(v)
                    else:
                        display.completed[observatory].add(v)
                        results.append(result)
                        if output:
                            io.update(fp, observatory, mjd, exposures, sequences, **io_kwds)

                    if live is not None and (time() - t) > 1 / refresh_per_second:
                        live.update(display.create_display())
                        t = time()

            if live is not None:
                live.update(display.create_display())
                if verbosity <= 1 and output is None:
                    sleep(3)

    if verbosity >= 2:
        for observatory, mjd, exposures, sequences in results:
            display_exposures(exposures, sequences)

    # Show critical logs at the end to avoid disrupting the display
        for item in buffered_critical_logs:
            logger.critical(item)


@main.command()
@click.argument("identifier", type=int)
@click.option("--careful", is_flag=True, help="Don't assume unique field for a given (obs, mjd, catalogid)")
def lookup(identifier, careful, **kwargs):
    """Lookup a target by catalog identifier or SDSS identifier."""

    if not identifier:
        return

    from peewee import fn
    from itertools import chain, starmap
    from almanac.database import database
    from almanac.apogee import get_exposures
    from sdssdb.peewee.sdss5db.targetdb import (
        Assignment, AssignmentStatus,CartonToTarget, Target, Hole, Observatory,
        Design, DesignToField
    )
    from sdssdb.peewee.sdss5db.catalogdb import SDSS_ID_flat

    from rich.table import Table as RichTable
    from rich.console import Console
    from rich.live import Live

    sq = (
        SDSS_ID_flat
        .select(SDSS_ID_flat.sdss_id)
        .where(
            (SDSS_ID_flat.sdss_id == identifier)
        |   (SDSS_ID_flat.catalogid == identifier)
        )
        .alias("sq")
    )
    q = (
        SDSS_ID_flat
        .select(SDSS_ID_flat.catalogid, SDSS_ID_flat.sdss_id)
        .distinct()
        .join(sq, on=(SDSS_ID_flat.sdss_id == sq.c.sdss_id))
        .tuples()
    )

    sdss_ids, catalogids = (set(), [])
    for catalogid, sdss_id in q:
        sdss_ids.add(sdss_id)
        catalogids.append(catalogid)

    if not catalogids:
        raise click.ClickException(f"Identifier {identifier} not found in SDSS-V database")

    if len(sdss_ids) != 1:
        raise click.ClickException(f"Identifier {identifier} is ambiguous and matches multiple SDSS IDs: {', '.join(map(str, sdss_ids))}")

    q = (
        Target
        .select(
            fn.Lower(Observatory.label),
            AssignmentStatus.mjd,
        )
        .join(CartonToTarget)
        .join(Assignment)
        .join(AssignmentStatus)
        .switch(Assignment)
        .join(Hole)
        .join(Observatory)
        .where(
            Target.catalogid.in_(tuple(catalogids))
        &   (AssignmentStatus.status == 1)
        )
        .tuples()
    )
    q = tuple(set([(obs, int(mjd)) for obs, mjd in q]))

    console = Console()

    title = f"SDSS ID {sdss_id}"

    # Create Rich table
    rich_table = RichTable(title=f"{title}", title_style="bold blue", show_header=True, header_style="bold cyan")

    for field_name in ("#", "obs", "mjd", "exposure", "field", "fiber_id", "catalogid"):
        rich_table.add_column(field_name, justify="center")

    fields = {}
    i = 1
    with Live(rich_table, console=console, refresh_per_second=4) as live:
        for exposure in chain(*starmap(get_exposures, q)):
            key = (exposure.observatory, exposure.mjd)
            if (key not in fields or fields[key] == exposure.field_id) or careful:
                for target in exposure.targets:
                    if target.catalogid in catalogids:
                        fields[key] = exposure.field_id
                        rich_table.add_row(*list(map(str, (
                            i,
                            exposure.observatory,
                            exposure.mjd,
                            exposure.exposure,
                            exposure.field_id,
                            target.fiber_id,
                            target.catalogid
                        ))))
                        i += 1
                        break


@main.group()
def add(**kwargs):
    """Add new information to an existing Almanac file."""
    pass

@add.command()
@click.argument("input_path", type=str)
@click.option("--mjd", default=None, type=int, help="Modified Julian date to query. Use negative values to indicate relative to current MJD")
@click.option("--mjd-start", default=None, type=int, help="Start of MJD range to query")
@click.option("--mjd-end", default=None, type=int, help="End of MJD range to query")
@click.option("--date", default=None, type=str, help="Date to query (e.g., 2024-01-15)")
@click.option("--date-start", default=None, type=str, help="Start of date range to query")
@click.option("--date-end", default=None, type=str, help="End of date range to query")
@click.option("--apo", is_flag=True, help="Query Apache Point Observatory data")
@click.option("--lco", is_flag=True, help="Query Las Campanas Observatory data")
def metadata(input_path, mjd, mjd_start, mjd_end, date, date_start, date_end, apo, lco, **kwargs):
    """Add astrometry and photometry to an existing Almanac file."""

    import numpy as np
    import h5py as h5
    from itertools import product
    from almanac import utils
    from almanac.catalog import query_catalog
    from almanac.data_models.metadata import SourceMetadata
    from tqdm import tqdm

    observatories = utils.get_observatories(apo, lco)
    mjds, *_ = utils.parse_mjds(
        mjd, mjd_start, mjd_end, date, date_start, date_end, return_nones=True
    )

    sdss_ids = set()
    with h5.File(input_path, "r") as fp:
        if mjds is None:
            mjds = []
            for obs in observatories:
                mjds.extend(fp[obs])
            mjds = list(set(mjds))

        for mjd, obs in product(mjds, observatories):
            group = fp.get(f"{obs}/{mjd}/fibers", [])
            for config in group:
                if "source_id" in group[config]:
                    continue
                sdss_ids.update(group[config]["sdss_id"][:])

    v = []
    for row in tqdm(query_catalog(sdss_ids), total=len(sdss_ids)):
        v.append(row)




        if mjd is None:
            total = sum([len(fp[obs].keys()) for obs in observatories])
        else:
            total = 1 * len(observatories)

        sdss_ids = dict()
        with tqdm(total=total, desc="Collecting SDSS identifiers") as pb:
            for observatory in observatories:
                if observatory not in fp:
                    continue

                mjds = fp[observatory].keys() if mjd is None else [str(mjd)]

                for mjd in mjds:
                    group = fp[f"{observatory}/{mjd}"]
                    if "fibers" not in group:
                        continue

                    for config_id in group["fibers"]:
                        config_group = group[f"fibers/{config_id}"]

                        if "source_id" in config_group:
                            continue

                        dtypes = dict(
                            sdss_id=(np.int64, -1),
                            source_id=(np.int64, -1),
                            ra=(float, np.nan),
                            dec=(float, np.nan),
                            parallax=(float, np.nan),
                            radial_velocity=(float, np.nan),
                            radial_velocity_error=(float, np.nan),
                            bp_rp=(float, np.nan),
                            bp_g=(float, np.nan),
                            g_rp=(float, np.nan),
                            designation=(None, ""),
                            j_m=(float, np.nan),
                            h_m=(float, np.nan),
                            k_m=(float, np.nan),
                        )

                        n = len(config_group["sdss_id"][:])
                        metadata = {k: [v[1]] * n for k, v in dtypes.items()}
                        for i, row in enumerate(query_catalog(list(config_group["sdss_id"][:]))):
                            for key in row.keys():
                                metadata[key][i] = row[key]

                        # match to existing sdss_id
                        new_id = np.argsort(np.argsort(config_group["sdss_id"][:]))
                        indices = np.argsort(metadata["sdss_id"])[new_id]

                        for key, values in metadata.items():
                            if key in config_group:
                                continue
                            dtype, default = dtypes[key]
                            values = np.array([v or default for v in values], dtype=dtype)[indices]
                            if key == "designation":
                                values = list(map(str, values))
                            config_group.create_dataset(key, data=values, dtype=dtype)
                            print(f"Created {observatory}/{mjd}/fibers/{config_id}/{key}")
                    pb.update(1)


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


@config.command(hidden=True)
@click.argument("key")
@click.argument("value")
def update(key, value, **kwargs):
    """Update a configuration value"""
    click.echo(click.style("Deprecated: use `almanac config set`", fg="yellow"))
    return set(key, value, **kwargs)

@config.command(name="set")
@click.argument("key")
@click.argument("value")
def _set(key, value, **kwargs):
    """Set a configuration value"""

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
def check_paths_and_format(input_path, output_path, given_format, overwrite):
    import os
    import click

    if not os.path.exists(input_path):
        raise click.ClickException(f"Input path {input_path} does not exist")

    if os.path.exists(output_path) and not overwrite:
        raise click.ClickException(f"Output path {output_path} already exists. Use --overwrite to overwrite.")

    if given_format is None:
        if output_path.lower().endswith(".fits"):
            return "fits"
        elif output_path.lower().endswith(".csv"):
            return "csv"
        elif output_path.lower().endswith(".hdf5") or output_path.lower().endswith(".h5"):
            return "hdf5"
        else:
            raise click.ClickException("Cannot infer output format from output path. Please specify --format")
    return given_format


@dump.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option("--format", "-f", default=None, type=click.Choice(["fits", "csv", "hdf5"]), help="Output format")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file")
def stars(input_path, output_path, overwrite, format, **kwargs):
    """Create a star-level summary file"""

    import h5py as h5
    from copy import deepcopy
    from collections import Counter

    stars = {}
    default = dict(
        mjds_apo=set(),
        mjds_lco=set(),
        n_visits=0,
        n_visits_apo=0,
        n_visits_lco=0,
        n_exposures=0,
        n_exposures_apo=0,
        n_exposures_lco=0,
    )

    output_format = check_paths_and_format(input_path, output_path, format, overwrite)
    assert format != "hdf5", "HDF5 output not yet supported for star summaries."
    with h5.File(input_path, "r") as fp:
        for observatory in fp:
            for mjd in fp[f"{observatory}"]:
                group = fp[f"{observatory}/{mjd}"]

                is_object = (
                    (group["exposures/image_type"][:].astype(str) == "object")
                )
                fps = is_object * (group["exposures/config_id"][:] > 0)
                plate = is_object * (group["exposures/plate_id"][:] > 0)

                if not any(fps) and not any(plate) or "fibers" not in group:
                    continue

                # fps era
                n_exposures_on_this_mjd = {}

                if any(fps):
                    config_ids = Counter(group["exposures/config_id"][:][fps])
                elif any(plate):
                    config_ids = Counter(group["exposures/plate_id"][:][plate])
                else:
                    continue

                for config_id, n_exposures in config_ids.items():
                    try:
                        config_group = group[f"fibers/{config_id}"]
                    except KeyError:
                        print(f"Warning couldnt get config {config_id} for {observatory} {mjd}")
                        continue

                    ok = (
                        (
                            (config_group["catalogid"][:] > 0)
                        |   (config_group["sdss_id"][:] > 0)
                        |   (config_group["twomass_designation"][:].astype(str) != "")
                        )
                    *   (
                            (config_group["category"][:].astype(str) == "science")
                        |   (config_group["category"][:].astype(str) == "standard_apogee")
                        |   (config_group["category"][:].astype(str) == "standard_boss")
                        |   (config_group["category"][:].astype(str) == "open_fiber")
                        )
                    )
                    sdss_ids = config_group["sdss_id"][:][ok]
                    catalogids = config_group["catalogid"][:][ok]
                    for sdss_id, catalogid in zip(sdss_ids, catalogids):
                        stars.setdefault(sdss_id, deepcopy(default))
                        stars[sdss_id].setdefault("catalogid", catalogid) # this can change over time,... should we track that/
                        n_exposures_on_this_mjd.setdefault(sdss_id, 0)
                        n_exposures_on_this_mjd[sdss_id] += n_exposures


                for sdss_id, n_exposures in n_exposures_on_this_mjd.items():
                    stars[sdss_id]["n_exposures"] += n_exposures
                    stars[sdss_id][f"n_exposures_{observatory}"] += n_exposures
                    stars[sdss_id]["n_visits"] += 1
                    stars[sdss_id][f"n_visits_{observatory}"] += 1
                    stars[sdss_id][f"mjds_{observatory}"].add(int(mjd))

        rows = []
        for sdss_id, meta in stars.items():
            stars[sdss_id].update(
                mjd_min_apo=min(meta["mjds_apo"]) if meta["mjds_apo"] else -1,
                mjd_max_apo=max(meta["mjds_apo"]) if meta["mjds_apo"] else -1,
                mjd_min_lco=min(meta["mjds_lco"]) if meta["mjds_lco"] else -1,
                mjd_max_lco=max(meta["mjds_lco"]) if meta["mjds_lco"] else -1,
            )
            stars[sdss_id].pop("mjds_apo")
            stars[sdss_id].pop("mjds_lco")
            rows.append(dict(sdss_id=sdss_id, **meta))

    from astropy.table import Table
    t = Table(rows=rows)
    t.write(output_path, format=output_format, overwrite=overwrite)



@dump.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option("--format", "-f", default=None, type=click.Choice(["fits", "csv", "hdf5"]), help="Output format")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file")
def visits(input_path, output_path, format, overwrite, **kwargs):
    """Create a visit-level summary file"""

    pass



@dump.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option("--format", "-f", default=None, type=click.Choice(["fits", "csv", "hdf5"]), help="Output format")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file")
def exposures(input_path, output_path, format, overwrite, **kwargs):
    """Create an exposure-level summary file"""

    import os
    import h5py as h5
    import numpy as np

    output_format = check_paths_and_format(input_path, output_path, format, overwrite)

    from almanac.data_models import Exposure

    fields = { **Exposure.model_fields, **Exposure.model_computed_fields }
    data = dict()
    for field_name, field_spec in fields.items():
        data[field_name] = []

    with h5.File(input_path, "r") as fp:
        for observatory in ("apo", "lco"):
            for mjd in fp[observatory].keys():
                group = fp[f"{observatory}/{mjd}/exposures"]
                for key in group.keys():
                    data[key].extend(group[key][:])

    if output_format == "hdf5":
        from almanac.io import _write_models_to_hdf5_group

        fields = { **Exposure.model_fields, **Exposure.model_computed_fields }

        with h5.File(output_path, "w", track_order=True) as fp:
            _write_models_to_hdf5_group(fields, data, fp)
    else:
        from astropy.table import Table
        t = Table(data=data)
        t.write(output_path, format=output_format, overwrite=overwrite)


@dump.command()
@click.argument("input_path", type=str)
@click.argument("output_path", type=str)
@click.option("--format", "-f", default=None, type=click.Choice(["fits", "csv", "hdf5"]), help="Output format")
@click.option("--overwrite", is_flag=True, help="Overwrite existing output file")
def fibers(input_path, output_path, format, overwrite, **kwargs):
    """Create a fiber-level summary file"""

    import os
    import h5py as h5
    import numpy as np

    output_format = check_paths_and_format(input_path, output_path, format, overwrite)

    from almanac.data_models.fps import FPSTarget
    from almanac.data_models.plate import PlateTarget

    fields = { **FPSTarget.model_fields, **FPSTarget.model_computed_fields,
              **PlateTarget.model_fields, **PlateTarget.model_computed_fields }

    defaults = { name: spec.default for name, spec in fields.items() if hasattr(spec, "default") }
    defaults["twomass_designation"] = ""

    data = dict()
    for field_name, field_spec in fields.items():
        data[field_name] = []

    with h5.File(input_path, "r") as fp:
        for observatory in ("apo", "lco"):
            for mjd in fp[observatory].keys():
                group = fp[f"{observatory}/{mjd}/fibers"]
                for config_id in group.keys():
                    group = fp[f"{observatory}/{mjd}/fibers/{config_id}"]
                    n = len(group["sdss_id"][:])

                    for field_name in data:
                        if field_name in group.keys():
                            data[field_name].extend(group[field_name][:])
                        else:
                            data[field_name].extend([defaults[field_name]] * n)

    if output_format == "hdf5":
        from almanac.io import _write_models_to_hdf5_group

        with h5.File(output_path, "w", track_order=True) as fp:
            _write_models_to_hdf5_group(fields, data, fp)
    else:
        from astropy.table import Table
        t = Table(data=data)
        t.write(output_path, format=output_format, overwrite=overwrite)


if __name__ == "__main__":
    main()
