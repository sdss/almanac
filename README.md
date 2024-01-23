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

```python
almanac
almanac --apo # Apache Point Observatory
almanac --lco # Las Campanas Observatory
```

## Specifying a date

If you want a particular day, either use the ``--mjd`` or ``--date`` (UTC) flags:

```python
almanac --mjd 59300
almanac --date 2021-01-01
```

You can also specify a range of days:

```python
almanac --mjd 59300 59310 # Give me these 10 days
almanac --date 2021-01-01 2021-01-31 # Give me all of January 2021
```

## Fiber mappings

You can also use `almanac` to see the fiber mappings for a given plate (SDSS-IV) or FPS pointing (SDSS-V) by specifing the ``--fibres`` flag. This will give you the mapping of fibers to targets, and the target properties. 

```python
almanac --mjd 60000 --fibres
```

The SDSS identifiers (`sdss_id`) are not included in the fibre mapping tables by default. When you use the ``--fibres`` flag this will automatically include a cross-match to the database to assign SDSS identifiers to every target. You can disable this option with ``--no-x-match``. The ``--no-x-match`` flag is ignored if ``--fibres`` is not used.

## Output behaviour

By default the output will appear in a pretty way in the terminal. Instead you can specify an output path with the ``--output`` (or ``-O``) flag. If the output path already exists, the default behaviour is to append unique entries. You can overwrite the file with the ``--overwrite`` flag.

```python
almanac --output /path/to/file.h5 # Append today's data to existing file
almanac --output /path/to/file.h5 --overwrite # Overwrite today's data to existing file
```