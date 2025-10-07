#!/usr/bin/env python3
"""
Combine output metadata from APOGEE spectra reduced with ApogeeReductions.jl and
arMADGICS.jl into a single HDF5 file.
"""

import h5py
import os
import numpy as np

observatory = "apo"
mjd = 58562

output_file = "temp.h5"


files_1d = [
    'arMADGICS_out_RV_flag.h5',
    'arMADGICS_out_RV_minchi2_final.h5',
    'arMADGICS_out_RV_pix_var.h5',
    'arMADGICS_out_RV_pixoff_disc_final.h5',
    'arMADGICS_out_RV_pixoff_final.h5',
    'arMADGICS_out_RVchi2_residuals.h5',
    'arMADGICS_out_adjfiberindx.h5',
    'arMADGICS_out_avg_flux_conservation.h5',
    'arMADGICS_out_data_pix_cnt.h5',
    'arMADGICS_out_final_pix_cnt.h5',
    'arMADGICS_out_flux_nans.h5',
    'arMADGICS_out_fluxerr2_nans.h5',
    'arMADGICS_out_skyscale0.h5',
    'arMADGICS_out_skyscale1.h5',
    'arMADGICS_out_starscale.h5',
    'arMADGICS_out_starscale1.h5',
    'arMADGICS_out_tot_p5chi2_v0.h5',
]

# Base directory containing the HDF5 files
outdir = '/mnt/ceph/users/sdssv/work/asaydjari/2025_10_01/outdir'

armadgics_dir = f'{outdir}/arMADGICS/'
batch_info_file = f'{armadgics_dir}/raw_{observatory}_{mjd}/batch_info.txt'

print(f"Creating combined HDF5 file: {output_file}")

# Read batch_info.txt
print(f"Reading batch info from {batch_info_file}")
batch_info = np.loadtxt(
    batch_info_file,
    skiprows=5,
    dtype=[
        ("linear_index", int),
        ("observatory", "|S3"),
        ("mjd", int),
        ("exposure", int),
        ("adjusted_fiber_index", int)
    ],
    delimiter=",",
    converters={1: lambda x: x.strip()}
)

n = len(batch_info)
print(f"  Read {n} entries from batch_info.txt")

fp = h5py.File(output_file, 'w')
if True:
    group = fp.create_group(f"{observatory}/{mjd}", track_order=True)
    print(f"Created group: {observatory}/{mjd}")

    # Add batch info datasets
    print("Adding batch info datasets:")
    for field_name in ("linear_index", "observatory", "mjd", "exposure", "adjusted_fiber_index"):
        group.create_dataset(field_name, data=np.array(batch_info[field_name]))
        print(f"  Added: {field_name} from batch_info.txt")

    # Add 1D arrays from HDF5 files
    for basename in files_1d:
        fpath = os.path.join(
            armadgics_dir,
            f"wu_th_{observatory}_{mjd}",
            basename
        )
        if not os.path.exists(fpath):
            print(f"Warning: {basename} not found, skipping...")
            raise a
            continue

        with h5py.File(fpath, 'r') as in_f:
            # Find the dataset (exclude 'hdr')
            for key in in_f.keys():
                if key != 'hdr':
                    dataset = in_f[key]
                    # Verify it's 1D with size n
                    if dataset.ndim == 1 and dataset.shape[0] == n:
                        group.create_dataset(key, data=dataset[:])
                        print(f"  Added: {key} from {basename}")
                    else:
                        print(f"  Skipped: {key} (shape {dataset.shape})")


print(f"\nDone! Created {output_file}")
