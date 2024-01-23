# almanac

![Versions](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/almanac/badge/?version=latest)](https://almanac.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/sdss/almanac/branch/main/graph/badge.svg)](https://codecov.io/gh/sdss/almanac)

Everything we've got.


# Installation

`almanac` needs local disk access to the raw SDSS data frames. If you want to use this at Utah, you can install it with:

```bash
module load almanac
```

# Usage

Use `almanac` to see details on data taken from both observatories in the last 24 hours, or specify the observatory:

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

You can also specify a range of days:

```bash
almanac --mjd 59300 59310 # Give me these 10 days
almanac --date 2021-01-01 2021-01-31 # Give me all of January 2021
```

## Fiber mappings

You can also use `almanac` to see the fiber mappings for a given plate (SDSS-IV) or FPS pointing (SDSS-V) by specifing the ``--fibres`` flag. This will give you the mapping of fibers to targets, and the target properties. 

```bash
almanac --mjd 60000 --fibres
```

The SDSS identifiers (`sdss_id`) are not included in the fibre mapping tables by default. When you use the ``--fibres`` flag this will automatically include a cross-match to the database to assign SDSS identifiers to every target. You can disable this option with ``--no-x-match``. The ``--no-x-match`` flag is ignored if ``--fibres`` is not used.

## Exposure sequences

You can also use `almanac` to group exposures of the same pointing that were taken in sequence. This is useful for checking which exposures should be associated to describe a single visit. Use the ``--sequences`` flag to add sequences for the given data.

```bash
almanac --apo --sequences
```

## Output behaviour

By default the output will appear in a pretty way in the terminal. Instead you can specify an output path with the ``--output`` (or ``-O``) flag. If the output path already exists, the default behaviour is to append unique entries. You can overwrite the file with the ``--overwrite`` flag.

```bash
almanac --output /path/to/file.h5 # Append today's data to existing file
almanac --output /path/to/file.h5 --overwrite # Overwrite today's data to existing file
```

## Keeping a local record up to date

If you are wanting to keep a local record up to date, including all fibre mappings and exposure sequences, then the daily command you are looking for is probably:

```bash
almanac --fibres --sequences --output /path/to/file.h5
```

This will append today's data to the output path, and will include the fibre mappings and exposure sequences. If you want to overwrite the file with just data taken from today, add the ``--overwrite`` flag.