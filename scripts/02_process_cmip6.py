from pathlib import Path
import sys

from tqdm import tqdm
import yaml

from wildfire_analysis.data.process_cmip6 import process_cmip6

# Get global values from configuration file
config_fn = Path(__file__).parent / '../wildfire_analysis/config.yaml'
with open(config_fn,'r') as config_file:
    config_params = yaml.safe_load(config_file)

raw_data_dir = Path(config_params['PATHS']['raw_data_dir'])
processed_data_dir = Path(config_params['PATHS']['processed_data_dir'])
gcm_list = config_params['CLIMATE']['gcm_list']
metvars = config_params['CLIMATE']['metvars']
cmip6_yr = config_params['TIME']['cmip6_yr']

verbose = False
if sys.argv[-1] == '--verbose':
    verbose = True

# Convert to range
cmip6_yr = range(cmip6_yr[0],cmip6_yr[1]+1)

# ERA5 file to extract lat/lon coords and use for regridding
coords = processed_data_dir / 'climate/era5/tasmax_era5_1979.nc'

N = len(gcm_list) * len(metvars)

with tqdm(total=N,disable=not verbose) as pbar: # for progress bar

    for gcm in gcm_list:

        wdir = raw_data_dir / 'climate/cmip6' / gcm
        dest = processed_data_dir / 'climate/cmip6' / gcm

        if not dest.exists():
            dest.mkdir(parents=True)
        
        for var in metvars:

            if (var == 'sfcWind'):

                src = list(wdir.glob('?as_*nc'))

            else:

                src = list(wdir.glob('%s*nc' % var))

            ds = process_cmip6(src)
            ds = ds.compute()

            for yr in cmip6_yr:

                fn = dest / ('%s_%s_%d.nc' % (var,gcm,yr))
                ds_i = ds.sel(time=slice(str(yr),str(yr)))

                ds_i.to_netcdf(fn,engine='h5netcdf')

            pbar.update()
            
            del ds