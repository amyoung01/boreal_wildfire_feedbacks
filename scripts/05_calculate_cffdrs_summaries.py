#%% Import libraries
from pathlib import Path
import sys

from tqdm import tqdm
import xarray as xr
import yaml

from wildfire_analysis.data_processing import cffdrs_stats

#%% Import config file and read in parameters needed for data processing
config_fn = Path(__file__).parent / '../wildfire_analysis/config.yaml'
with open(config_fn,'r') as config_file:   
    config_params = yaml.safe_load(config_file)

    processed_data_dir = Path(config_params['PATHS']['processed_data_dir'])
    gcm_list = config_params['CLIMATE']['gcm_list']
    era5_yr = config_params['TIME']['era5_yr']
    hst_yr = config_params['TIME']['hst_yr']
    sim_periods = config_params['TIME']['sim_periods']

#%% If verbose=True then have progress bar document processing time
verbose = False
if sys.argv[-1] == '--verbose':
    verbose = True

#%% Set working directories for reading in climate data
era5_dir = processed_data_dir / 'cffdrs/era5'
cmip6_dir = processed_data_dir / 'cffdrs/cmip6'

#%% Create era5 and cmip6 destination directories (if they don't exist)
dest = processed_data_dir / 'cffdrs/cffdrs_stats/'
if dest.exists() is False:
    dest.mkdir(parents=True)

#%% Convert yrs to ranges
era5_yr = range(era5_yr[0],era5_yr[1]+1)
cmip6_yr = range(hst_yr[0],sim_periods[-1][1]+1)

#%% Process and calculate cffdrs for era5 data
if verbose:
    print('\n\n--------------------------------------------------------------')
    print('Processing and calculating CFFDRS statistics for era5 data ...')

filelist = [list(era5_dir.glob("*%d*" % i))[0] for i in era5_yr]    
ds_cffdrs_stats = cffdrs_stats(filelist)

era5_fn = dest / ('cffdrs-stats_era5_%d-%d.nc' % (era5_yr[0],era5_yr[-1]))
ds_cffdrs_stats.to_netcdf(era5_fn,engine='h5netcdf')

if verbose:
    print('... finished!')
    print('--------------------------------------------------------------')    

# if verbose:
#     print('\n\n--------------------------------------------------------------')
#     print('Processing and calculating CFFDRS statistics for era5 data ...')

# for gcm in gcm_list:

