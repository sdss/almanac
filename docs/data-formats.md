# Data Formats

This document describes the data formats used by `almanac`, particularly the HDF5 output structure and data schemas.

## HDF5 Output Structure

`almanac` stores data in HDF5 format with a hierarchical structure that organizes data by observatory and Modified Julian Date (MJD).

### Directory Structure

```
filename.h5
├── apo/                    # Apache Point Observatory
│   ├── 59300/             # MJD 59300
│   │   ├── exposures      # Exposure metadata table
│   │   ├── sequences      # Exposure sequence indices
│   │   └── fibers/        # Fiber mapping data
│   │       ├── fps/       # Fiber Positioner System (SDSS-V)
│   │       │   ├── 1      # Configuration ID 1
│   │       │   └── 2      # Configuration ID 2
│   │       └── plates/    # Plate-based system (SDSS-IV)
│   │           ├── 15001  # Plate ID 15001
│   │           └── 15002  # Plate ID 15002
│   └── 59301/             # MJD 59301
└── lco/                   # Las Campanas Observatory
    └── 59300/
        ├── exposures
        ├── sequences
        └── fibers/
```

## Data Tables

### Exposure Table

The `exposures` table contains metadata for all exposures taken on a given MJD.

#### Core Columns

| Column | Type | Description |
|--------|------|-------------|
| `observatory` | string | Observatory code ("apo" or "lco") |
| `mjd` | int | Modified Julian Date |
| `exposure` | int | Exposure number |
| `exptype` | string | Exposure type (e.g., "OBJECT", "FLAT", "ARC") |
| `nread` | int | Number of detector reads |

#### Configuration Columns

| Column | Type | Description |
|--------|------|-------------|
| `configid` | int | FPS configuration ID (SDSS-V) |
| `designid` | int | Survey design ID |
| `fieldid` | int | Field identifier |
| `cartid` | int | Cartridge ID (SDSS-IV) |
| `plateid` | int | Plate ID (SDSS-IV) |

#### Instrumental Columns

| Column | Type | Description |
|--------|------|-------------|
| `lampqrtz` | bool | Quartz lamp status |
| `lampthar` | bool | ThAr lamp status |  
| `lampune` | bool | UNe lamp status |
| `focus` | float | Focus position |
| `dithpix` | float | Dither pixels |

#### Observational Columns

| Column | Type | Description |
|--------|------|-------------|
| `seeing` | float | Seeing in arcseconds |
| `date_obs` | string | Observation date/time |
| `imagetyp` | string | Image type |
| `obscmt` | string | Observer comments |

### Sequence Table

The `sequences` table is an Nx2 array defining exposure sequences.

| Column | Type | Description |
|--------|------|-------------|
| Start | int | First exposure number in sequence |
| End | int | Last exposure number in sequence (inclusive) |

Each row represents a continuous sequence of exposures that form a logical observational unit.

## Fiber Mapping Data

Fiber mapping tables connect fibers to astronomical targets with different schemas for SDSS-IV (plates) and SDSS-V (FPS).

### FPS (Fiber Positioner System) - SDSS-V

Located at: `fibers/fps/{configid}`

#### Target Identification

| Column | Type | Description |
|--------|------|-------------|
| `sdss_id` | int64 | SDSS unique identifier |
| `catalogid` | int64 | Catalog identifier |
| `target_id` | int64 | Target identifier |

#### Survey Information

| Column | Type | Description |
|--------|------|-------------|
| `program` | string | Survey program name |
| `category` | string | Target category |
| `firstcarton` | string | Primary target carton |
| `cadence` | string | Observing cadence |

#### Coordinates and Properties

| Column | Type | Description |
|--------|------|-------------|
| `ra` | float64 | Right ascension (degrees) |
| `dec` | float64 | Declination (degrees) |
| `pmra` | float32 | Proper motion in RA (mas/yr) |
| `pmdec` | float32 | Proper motion in Dec (mas/yr) |
| `parallax` | float32 | Parallax (mas) |

#### Fiber Assignment

| Column | Type | Description |
|--------|------|-------------|
| `fiberId` | int32 | Fiber identifier |
| `assigned` | bool | Whether fiber is assigned to target |
| `on_target` | bool | Whether fiber is on intended target |

#### Photometry

| Column | Type | Description |
|--------|------|-------------|
| `g` | float32 | SDSS g magnitude |
| `r` | float32 | SDSS r magnitude |
| `i` | float32 | SDSS i magnitude |
| `z` | float32 | SDSS z magnitude |
| `h` | float32 | 2MASS H magnitude |

### Plates - SDSS-IV

Located at: `fibers/plates/{plateid}`

#### Target Identification

| Column | Type | Description |
|--------|------|-------------|
| `sdss_id` | int64 | SDSS unique identifier |
| `target_id` | int64 | Target identifier |

#### Coordinates

| Column | Type | Description |
|--------|------|-------------|
| `target_ra` | float64 | Target RA (degrees) |
| `target_dec` | float64 | Target Dec (degrees) |

#### Classification

| Column | Type | Description |
|--------|------|-------------|
| `target_type` | string | Target type classification |
| `source_type` | string | Source type classification |

#### Fiber Assignment  

| Column | Type | Description |
|--------|------|-------------|
| `fiber_id` | int32 | Fiber identifier |

## Data Access Patterns

### Reading HDF5 Files

**Python Example**:
```python
import h5py
import pandas as pd

# Open HDF5 file
with h5py.File('almanac_data.h5', 'r') as f:
    # Read exposures for APO MJD 59300
    exposures = pd.read_hdf('almanac_data.h5', 'apo/59300/exposures')
    
    # Read FPS fiber mappings
    fibers = pd.read_hdf('almanac_data.h5', 'apo/59300/fibers/fps/1')
    
    # Read sequences
    sequences = f['apo/59300/sequences'][:]
```

### Incremental Updates

When `almanac` writes to an existing HDF5 file:
- **Existing data**: Preserved unchanged
- **New MJD data**: Added to appropriate observatory/MJD groups  
- **Updated MJD data**: Overwrites existing entries for that MJD

This allows for incremental data collection and updates.

## Column Customization

### Command-Line Control

Users can control which columns are included using command-line options:

```bash
# Custom exposure columns
almanac --exposure-columns "observatory,mjd,exposure,exptype,seeing"

# Custom FPS columns  
almanac --fps-columns "sdss_id,catalogid,ra,dec,fiberId"

# Custom plate columns
almanac --plate-columns "sdss_id,target_ra,target_dec,fiber_id"
```

### Available Column Sets

**Exposure Columns**: All columns from the exposure metadata table
**FPS Columns**: All columns from FPS fiber mapping tables
**Plate Columns**: All columns from plate fiber mapping tables

Use `"all"` to include all available columns for any table type.

## Data Quality

### Missing Values

- **Numeric columns**: Missing values represented as NaN
- **String columns**: Missing values as empty strings or "N/A"
- **Boolean columns**: Missing values as False

### Data Validation

`almanac` performs basic validation:
- Date/time format consistency
- Numeric range checking
- Required field presence

### Cross-Matching Status

When `--no-x-match` is used:
- SDSS identifier fields may be missing or incomplete
- Target properties from database may be unavailable
- Processing is faster but less comprehensive

## Compression

HDF5 files use compression by default:
- **Algorithm**: gzip compression
- **Level**: Default compression level
- **Benefits**: Reduced file size, maintained read performance

Compression can be controlled in the API but not via command-line interface.

## File Size Estimates

Typical file sizes (uncompressed/compressed):

- **Single MJD, exposures only**: ~10 KB / ~3 KB
- **Single MJD with fibers**: ~1-10 MB / ~200 KB - 2 MB  
- **Monthly data with fibers**: ~50-500 MB / ~10-100 MB
- **Annual survey data**: ~1-10 GB / ~200 MB - 2 GB

Actual sizes depend on:
- Number of exposures per night
- Number of configured fibers
- Selected column sets
- Target density and metadata completeness