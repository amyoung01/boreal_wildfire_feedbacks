#!/usr/bin/env python3

#%% Import libraries
from pathlib import Path
import sys

import yaml

from wildfire_analysis.data_processing import cffdrs_stats
from wildfire_analysis.utils import helpers as h

#%% Import config file and read in parameters needed for data processing
root_dir = Path(h.get_root_dir())
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:   
    config_params = yaml.safe_load(config_file)

    processed_data_dir = root_dir / config_params['PATHS']['processed_data_dir']
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

#%% Convert yrs to ranges. Start cmip6_yr at first yr of historical period
# to provide years for historical reference (e.g. maximum anomaly relative to
# 1980-2009)
era5_yr = range(era5_yr[0],era5_yr[1]+1)
cmip6_yr = range(hst_yr[0],sim_periods[-1][1]+1)

#%% Process and calculate cffdrs statistical summaries for era5 data
if verbose:
    print('\n\n--------------------------------------------------------------')
    print('Processing and calculating CFFDRS statistics for ERA5 data ...')

filelist = [list(era5_dir.glob("*%d*" % i))[0] for i in era5_yr]
ds_cffdrs_stats = cffdrs_stats.calc_fireweather_stats(filelist)
ds_cffdrs_stats = ds_cffdrs_stats[['isi','bui','fwi']]
ds_cffdrs_stats = ds_cffdrs_stats.astype('float32')
ds_cffdrs_stats = ds_cffdrs_stats.compute()

era5_fn = dest / ('cffdrs-stats_era5_%d-%d.nc' % (era5_yr[0],era5_yr[-1]))
ds_cffdrs_stats.to_netcdf(era5_fn,engine='h5netcdf')

if verbose:
    print('... finished!')
    print('--------------------------------------------------------------')    

#%% Process and calculate cffdrs statistical summaries for cmip6 datasets
if verbose:
    print('\n\n--------------------------------------------------------------')
    print('Processing and calculating CFFDRS statistics for CMIP6 data ...')

for gcm in gcm_list:

    if verbose:
        print('... working on %s ...' % gcm,end='') 

    gcm_dir_i = cmip6_dir / ('%s' % gcm)
    filelist = [list(gcm_dir_i.glob("*%d*" % i))[0] for i in cmip6_yr]
    ds_cffdrs_stats = cffdrs_stats.calc_fireweather_stats(filelist)
    ds_cffdrs_stats = ds_cffdrs_stats[['isi','bui','fwi']]
    ds_cffdrs_stats = ds_cffdrs_stats.astype('float32')

    gcm_fn = dest / ('cffdrs-stats_%s_%d-%d.nc' % 
                     (gcm,cmip6_yr[0],cmip6_yr[-1]))
    ds_cffdrs_stats.to_netcdf(gcm_fn,engine='h5netcdf')

    if verbose:
        print('... done! Now, ...') 

if verbose:
    print('\n... finished processing CFFFDRS stats for CMIP6!')
    print('--------------------------------------------------------------')

# %%
