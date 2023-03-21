"""
This module provides a set of functions to read in, organize, do unit
conversions on, and export GCM data needed for analysis.
"""

from pathlib import Path

import dask
import xarray as xr
import xclim as xc # For unit conversions
import yaml
from numpy import square, sqrt # For calculating wind speed from u, v vectors

from wildfire_analysis.utils import helpers as h

# Get global values from configuration file
config_fn = Path(h.get_root_dir()) / 'config.yaml'

with open(config_fn,'r') as config_file:

    config_params = yaml.safe_load(config_file)
    
    geo_lims = config_params['EXTENT']['geog_lims']

# Suppress dask warnings on chunk size
dask.config.set({"array.slicing.split_large_chunks": False})

# General processing of CMIP6 data
def _organize_cmip(ds):

    # Variable/coordinates not needed and can drop
    vars_to_drop = ['height','time_bnds','lat_bnds','lon_bnds','time_bounds',
                    'lat_bounds','lon_bounds']

    vars_in_ds = h.get_var_names(ds) + list(ds.coords)

    # Step 1: drop unnecessary variables
    ds = ds.drop_vars(list(set(vars_in_ds) & set(vars_to_drop)))

    # Step 2: reorganize lon to -180 thru 180
    lon_attrs = ds['lon'].attrs
    ds = ds.assign_coords(
        {'lon': ('lon',(((ds['lon'].values+180.0) % 360.0)-180.0))})
    ds = ds.sortby('lon')
    ds['lon'].attrs = lon_attrs

    # Step 3: clip geo limits
    ds = h.trim_geolims(ds,geo_lims)

    # Step 4: Convert calendar to 'noleap'
    ds = ds.convert_calendar('noleap')

    return ds

# Convert temperature to degrees C
def _process_tasmax(da):

    da = xc.units.convert_units_to(da,'degC')
    
    return da

# Convert precip to mm/day
def _process_pr(da):

     da = xc.units.convert_units_to(da,'mm/day')

     return da

# Calculate mean wind speed vector from u and v surface wind
def _process_sfcWind_from_uv(ds):

    # Convert to horizontal wind speed
    sfcWind = sqrt(square(ds['uas']) + square(ds['vas']))

    sfcWind.name = 'sfcWind'
    sfcWind.attrs = {
                    'units': 'm s**-1',
                    'standard_name': 'wind_speed',
                    'long_name': '10 metre horizonatal wind speed',
                    }

    return sfcWind

# Convert wind speed to km/hour
def _process_sfcWind(da):

    da = xc.units.convert_units_to(da,'km/hour')
    
    return da

# Ensure relative humidity is bounded between 0-100%
def _process_hursmin(da):

    da = da.clip(min=0.0,max=100.0)

    return da

# Process CMIP6 Dataset
def process_cmip6(src):

    da = xr.open_mfdataset(
        src,
        parallel=True,
        engine='h5netcdf',
        combine_attrs='drop_conflicts',
        mask_and_scale=True,
        )

    attrs = da.attrs

    n,p = (da['lat'].size,da['lon'].size)

    da = da.chunk(chunks={
        'time': 365,
        'lat': round(n/2),
        'lon': round(p/2),
        })

    da = _organize_cmip(da)

    standard_name = da[h.get_var_names(da)[0]].standard_name

    if standard_name == 'air_temperature':
        da = _process_tasmax(da['tasmax'])

    if standard_name == 'precipitation_flux':
        da = _process_pr(da['pr'])

    if (standard_name == 'eastward_wind' or
        standard_name == 'northward_wind'):
        da = _process_sfcWind_from_uv(da) # Calculate from u and v vectors
        da = _process_sfcWind(da) # Convert to km/hour

    if standard_name == 'wind_speed':
        da = _process_sfcWind(da['sfcWind'])        

    if standard_name == 'relative_humidity':
        da = _process_hursmin(da['hursmin'])

    ds = da.to_dataset()
    ds.attrs = attrs

    return ds

if __name__ == '__main__':    

    None
