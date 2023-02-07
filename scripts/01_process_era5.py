from pathlib import Path
import sys

from tqdm import tqdm
import yaml

from wildfire_analysis.data.process_era5 import process_era5
from wildfire_analysis.utils import helpers as h

# Get global values from configuration file
config_fn = Path(__file__).parent / '../wildfire_analysis/config.yaml'
with open(config_fn,'r') as config_file:
    config_params = yaml.safe_load(config_file)

raw_data_dir = Path(config_params['PATHS']['raw_data_dir'])
processed_data_dir = Path(config_params['PATHS']['processed_data_dir'])
era5_yr = config_params['TIME']['era5_yr']

verbose = False
if (sys.argv[-1] == "--verbose"):
    verbose = True

wdir = raw_data_dir / 'climate/era5/netcdf4'
dest = processed_data_dir / 'climate/era5'

# Convert to range
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