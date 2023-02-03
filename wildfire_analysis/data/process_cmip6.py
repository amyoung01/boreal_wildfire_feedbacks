"""

1. Drop unecessary variables
2. Convert lon limits to -180 thru 180 instead of 0-360
3. Clip geographic limits of gcm
4. Convert to 'noleap' calendar
5. Convert units (if necessary)
6. Export files for variables for single year

"""

import dask
import xarray as xr
import xclim as xc # For unit conversions

from numpy import square, sqrt # For calculating wind speed from u and v vectors

from wildfire_analysis.config import geo_lims
from wildfire_analysis.utils import helpers as h

# Suppress dask warnings on chunk size
dask.config.set({"array.slicing.split_large_chunks": False})

def organize_cmip(ds):

    vars_to_drop = ['height','time_bnds','lat_bnds','lon_bnds','time_bounds',
        'lat_bounds','lon_bounds']

    vars_in_ds = h.get_var_names(ds) + list(ds.coords)

    # Step 1: drop unnecessary variables
    ds = ds.drop_vars(list(set(vars_in_ds) & set(vars_to_drop)))

    # Step 2: reorganize lon to -180 thru 180
    lon_attrs = ds['lon'].attrs
    ds = ds.assign_coords({
        'lon': ('lon',(((ds['lon'].values + 180.0) % 360.0) - 180.0))
        })
    ds = ds.sortby('lon')
    ds['lon'].attrs = lon_attrs

    # Step 3: clip geo limits
    ds = h.trim_geolims(ds,geo_lims)

    # Step 4: Convert calendar to 'noleap'
    ds = ds.convert_calendar('noleap')

    return ds

def process_tasmax(da):

    da = xc.units.convert_units_to(da,'degC')
    
    return da

def process_pr(da):

     da = xc.units.convert_units_to(da,'mm/day')

     return da

def process_sfcWind_from_uv(ds):

    # Convert to horizontal wind speed
    sfcWind = sqrt(square(ds['uas']) + square(ds['vas']))

    sfcWind.name = 'sfcWind'
    sfcWind.attrs = {'units': 'm s**-1',
        'long_name': '10 metre horizonatal wind speed'}

    return sfcWind

def process_sfcWind(da):

    da = xc.units.convert_units_to(da,'km/hour')
    
    return da

def process_hursmin(da):

    da = da.clip(min=0.0,max=100.0)

    return da

def process_cmip(src):

    da = xr.open_mfdataset(
        src,
        parallel=True,
        engine='h5netcdf',
        combine_attrs='drop_conflicts',
        mask_and_scale=True
        )

    attrs = da.attrs

    n,p = (da['lat'].size,da['lon'].size)

    da = da.chunk(chunks={
            'time': 365,
            'lat': round(n/2),
            'lon': round(p/2)
            })

    da = organize_cmip(da)

    standard_name = da[h.get_var_names(da)[0]].standard_name

    if standard_name == 'air_temperature':
        da = process_tasmax(da['tasmax'])

    if standard_name == 'precipitation_flux':
        da = process_pr(da['pr'])

    if (standard_name == 'eastward_wind') | (standard_name == 'northward_wind'):
        da = process_sfcWind_from_uv(da) # Calculate from u and v vectors
        da = process_sfcWind(da) # Convert to km/hour

    if standard_name == 'wind_speed':
        da = process_sfcWind(da['sfcWind'])        

    if standard_name == 'relative_humidity':
        da = process_hursmin(da['hursmin'])

    ds = da.to_dataset()
    ds.attrs = attrs

    return ds

def main():

    return None

if __name__ == '__main__':    

    main()