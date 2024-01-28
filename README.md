# almanac

![Versions](https://img.shields.io/badge/python->3.7-blue)

Everything we've got.


# Installation

`almanac` needs local disk access to the raw SDSS data frames. 

If you want to use this at Utah, you can install it with:

```bash
module load almanac
```

> [!TIP]
> If you don't already have a Python environment set up at Utah that uses `sdssdb`, then you may want to run `module load miniconda` as well so that you have all the requisite dependencies.

# Usage

Use `almanac` to see details on data taken today from both observatories, or specify the observatory:

```bash
almanac
almanac --apo # Apache Point Observatory
almanac --lco # Las Campanas Observatory
```

## Specifying a date

If you want a particular day, either use the ``--mjd`` or ``--date`` (UTC) flags:

```bash
almanac --mjd 59300
almanac --date 2021-01-01
```

You can use negative MJD values to indicate days relative to today:

```bash
almanac --mjd -1 # Yesterday
almanac --mjd -7 # Last week
```

You can also specify a range of days:

```bash
almanac --mjd-start 59300 --mjd-end 59310 # Give me these 10 days
almanac --date-start 2021-01-01 --date-end 2021-01-31 # Give me all of January 2021
```

## Fiber mappings

You can also use `almanac` to see the fiber mappings for a given plate (SDSS-IV) or FPS pointing (SDSS-V) by specifing the ``--fibers`` (or ``--fibres``) flag. This will give you the mapping of fibers to targets, and the target properties. 

```bash
almanac --mjd 60000 --fibres
```

The fiber mapping tables are cross-matched to the SDSS database to include the SDSS identifiers for each target. If you don't want to do this cross-match, you can use the ``--no-x-match`` flag. The ``--no-x-match`` flag is ignored if ``--fibers`` is not used.


## Output behaviour

By default there is minimal output to the terminal. You can adjust the verbosity level using `-v`:
- `-v`: show progress bar only
- `-vv`: show progress bar and exposure metadata
- `-vvv`: show progress bar, exposure metadata, and fiber mapping metadata

You can also write the outputs to a structured HDF5 file by specifying an output path with the ``--output`` (or ``-O``) flag. If the output path already exists, the default behaviour is to overwrite existing entries *only*. So if you run `almanac` once for MJD 60000 and output to a file, and then run it again for MJD 60001 and output to the same file, your file will have data for both MJDs. 

```bash
almanac --output /path/to/file.h5 # Append today's data to existing file
```

An example structure of the HDF5 file is below:

```
    apo/59300/exposures         # a data table of exposures
    apo/59300/sequences         # a Nx2 array of exposure numbers (inclusive) that form a sequence
    apo/59300/fibers/fps/1      # a data table of fiber mappings for FPS configuration id 1
    apo/59300/fibers/plates/2   # a data table of fiber mappings for plate id 2
```
