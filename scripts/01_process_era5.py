import sys

from tqdm import tqdm

from wildfire_analysis.data.process_era5 import process_era5
from wildfire_analysis.config import raw_data_dir, processed_data_dir, era5_yr
from wildfire_analysis.utils import helpers as h

verbose = False
if (sys.argv[-1] == "--verbose"):
    verbose = True

wdir = raw_data_dir / 'climate/era5/netcdf4'
dest = processed_data_dir / 'climate/era5'

yr_range = range(era5_yr[0],era5_yr[1]+1)

with tqdm(total=len(yr_range),disable=not verbose) as pbar: # for progress bar

    for yr in yr_range:

        src = list(wdir.glob('%d*.nc' % yr))

        ds = process_era5(src,dask_load=True)

        for var in h.get_var_names(ds):

            fn = dest / ('%s_era5_%d.nc' % (var,yr))
            ds[var].to_netcdf(fn,engine='h5netcdf')

        # Close datasets
        ds.close()

        pbar.update()