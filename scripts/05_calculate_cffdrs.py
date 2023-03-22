#!/usr/bin/env python3

#%% Import libraries
from pathlib import Path
import sys

from tqdm import tqdm
import xarray as xr
import yaml

import wildfire_analysis.cffdrs as cffdrs
from wildfire_analysis.utils import helpers as h

#%% Import config file and read in parameters needed for data processing
# Get global values from configuration file
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
era5_dir = processed_data_dir / 'climate/era5'
cmip6_dir = processed_data_dir / 'climate/cmip6'

#%% Create era5 and cmip6 destination directories (if they don't exist)
era5_cffdrs_dir = processed_data_dir / 'cffdrs/era5'
if era5_cffdrs_dir.exists() is False:
    era5_cffdrs_dir.mkdir(parents=True)

for gcm in gcm_list:
    cmip6_cffdrs_dir_i = processed_data_dir / ('cffdrs/cmip6/%s' % gcm)
    if cmip6_cffdrs_dir_i.exists() is False:
        cmip6_cffdrs_dir_i.mkdir(parents=True)

#%% Convert yrs to ranges. Start cmip6_yr at first yr of historical period
# to provide years for historical reference (e.g. maximum anomaly relative to
# 1980-2009)
era5_yr = range(era5_yr[0],era5_yr[1]+1)
cmip6_yr = range(hst_yr[0],sim_periods[-1][1]+1)

#%% Process and calculate cffdrs for era5 data
if verbose:
    print('\n\n-------------------------------------------------------------')
    print('Processing and calculating CFFDRS indices for era5 data .....')
    print('-------------------------------------------------------------')

with tqdm(total=len(era5_yr),disable=not verbose) as pbar: # for progress bar

    for yr in era5_yr:

        # Get file list of era5 variables for a single year ...
        filelist = list(era5_dir.glob('*%d*nc' % yr))
        metvars = xr.open_mfdataset(filelist,engine='h5netcdf')

        # Transpose axes of data arrays to make sure they're in right order
        metvars = metvars.transpose('time','lat','lon')

        tas = metvars['tasmax'].values
        pr = metvars['pr'].values
        sfcWind = metvars['sfcWind'].values
        hurs = metvars['hursmin'].values
        mon = metvars['time'].dt.month.values

        # Calculate CFFDRS indices
        cffdrs_vals = cffdrs.cffdrs_calc(tas,pr,sfcWind,hurs,mon)

        # Put CFFDRS results in xarray dataset
        cffdrs_ds = xr.Dataset(
            data_vars={
                'ffmc': (['time','lat','lon'],cffdrs_vals['ffmc']),
                'dmc': (['time','lat','lon'],cffdrs_vals['dmc']),
                'dc': (['time','lat','lon'],cffdrs_vals['dc']),            
                'isi': (['time','lat','lon'],cffdrs_vals['isi']),
                'bui': (['time','lat','lon'],cffdrs_vals['bui']),
                'fwi': (['time','lat','lon'],cffdrs_vals['fwi']),
                },
            coords={
                'time': ('time',metvars['time'].values,
                         metvars['time'].attrs),
                'lat': ('lat',metvars['lat'].values,
                        metvars['lat'].attrs),
                'lon': ('lon',metvars['lon'].values,
                        metvars['lon'].attrs),
                })
        
        # Export/write CFFDRS results to netcdf file
        cffdrs_ds = cffdrs_ds.astype('float32')
        export_fn = era5_cffdrs_dir / ('cffdrs_era5_%d.nc' % yr)
        cffdrs_ds.to_netcdf(export_fn,engine='h5netcdf')

        pbar.update() # Update progress bar

#%% Process and calculate cffdrs for cmip6 data
if verbose:
    print('\n\n--------------------------------------------------------------')
    print('Processing and calculating CFFDRS indices for CMIP6 GCMs .....')
    print('--------------------------------------------------------------')

with tqdm(total=len(cmip6_yr)*len(gcm_list),disable=not verbose) as pbar:

    for gcm in gcm_list:

        cmip6_dir_i = cmip6_dir / ('%s/bias_corrected' % gcm)

        for yr in cmip6_yr:

            # Get file list of era5 variables for a single year ...
            filelist = list(cmip6_dir_i.glob('*%d*nc' % yr))
            metvars = xr.open_mfdataset(filelist,engine='h5netcdf')

            # Transpose axes of data arrays to make sure they're in right order
            metvars = metvars.transpose('time','lat','lon')

            # Get metvars as numpy arrays
            tas = metvars['tasmax'].values # Temperature
            pr = metvars['pr'].values # Precip
            sfcWind = metvars['sfcWind'].values # Wind speed
            hurs = metvars['hursmin'].values # Relative humidity
            mon = metvars['time'].dt.month.values # Months

            # Calculate CFFDRS indices
            cffdrs_vals = cffdrs.cffdrs_calc(tas,pr,sfcWind,hurs,mon)

            # Put CFFDRS results in xarray dataset
            cffdrs_ds = xr.Dataset(
                data_vars={
                    'ffmc': (['time','lat','lon'],cffdrs_vals['ffmc']),
                    'dmc': (['time','lat','lon'],cffdrs_vals['dmc']),
                    'dc': (['time','lat','lon'],cffdrs_vals['dc']),
                    'isi': (['time','lat','lon'],cffdrs_vals['isi']),
                    'bui': (['time','lat','lon'],cffdrs_vals['bui']),
                    'fwi': (['time','lat','lon'],cffdrs_vals['fwi']),
                    },
                coords={
                    'time': ('time',metvars['time'].values,
                             metvars['time'].attrs),
                    'lat': ('lat',metvars['lat'].values,
                            metvars['lat'].attrs),
                    'lon': ('lon',metvars['lon'].values,
                            metvars['lon'].attrs),
                    })
            
            # Export/write CFFDRS results to netcdf file
            cffdrs_ds = cffdrs_ds.astype('float32')
            export_fn = Path.joinpath(
                processed_data_dir,
                'cffdrs/cmip6/%s/cffdrs_%s_%d.nc' % (gcm,gcm,yr)
                )
            cffdrs_ds.to_netcdf(export_fn,engine='h5netcdf')

            pbar.update() # Update progress bar

if verbose:
    print('\n\nFinished calculating CFFDRS!\n\n')
