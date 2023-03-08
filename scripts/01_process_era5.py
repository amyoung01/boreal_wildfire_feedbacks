#!/usr/bin/env python3

#%% Import libraries
from pathlib import Path
import sys

from tqdm import tqdm
import yaml

from wildfire_analysis.data_processing.process_era5 import process_era5
from wildfire_analysis.utils import helpers as h

#%% Import config file and read in parameters needed for data processing
# Get global values from configuration file
root_dir = Path(h.get_root_dir())
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:
    config_params = yaml.safe_load(config_file)

    raw_data_dir = root_dir / config_params['PATHS']['raw_data_dir']
    processed_data_dir = root_dir / config_params['PATHS']['processed_data_dir']
    era5_yr = config_params['TIME']['era5_yr']

#%% Read in verbose flag to print progress bar
verbose = False
if (sys.argv[-1] == "--verbose"):
    verbose = True

#%% Set directories for reading and writing
wdir = raw_data_dir / 'climate/era5/netcdf4'
dest = processed_data_dir / 'climate/era5'

#%% Set range of years for processing
yr_range = range(era5_yr[0],era5_yr[1]+1)

with tqdm(total=len(yr_range),disable=not verbose) as pbar: # for progress bar

    for yr in yr_range: # For each year ...

        # Find file for given year
        src = list(wdir.glob('%d*.nc' % yr))

        # Process ERA5 datasets
        ds = process_era5(src,dask_load=True)

        # Export netcdf for each variable in a given year
        for var in h.get_var_names(ds):

            fn = dest / ('%s_era5_%d.nc' % (var,yr))
            ds[var].to_netcdf(fn,engine='h5netcdf')

        # Close datasets
        ds.close()

        pbar.update()