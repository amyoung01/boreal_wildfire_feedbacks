"""
Set of helper functions for various tasks in boreal_fire_feedbacks
project.

"""

import datetime as dt
from keyword import kwlist
import os
import pathlib

import cf_xarray
import geopandas as gpd
import numpy as np
import shapely.vectorized
import xarray as xr

def get_kwargs(x,kwargs):
    
    return {k:kwargs[k] for k in x if k in kwargs}

def get_var_names(ds):

    # Return list of all variable names in netcdf dataset
    return list(ds.keys())

def trim_geolims(ds,geolims):

    coord_names = get_coord_names(ds)

    lonlim = (geolims[0],geolims[2])
    latlim = (geolims[1],geolims[3])

    ds = ds.sortby(coord_names['lat'])

    sel_dict = {coord_names['lat']: slice(latlim[0],latlim[1]),
                coord_names['lon']: slice(lonlim[0],lonlim[1])}
    
    ds = ds.loc[sel_dict]

    return ds

def get_coord_names(ds):

    datavar = get_var_names(ds) # Get list of variables in dataset
    datavar = datavar[0] # Get first variable name
    coord_names = ds[datavar].dims # Get coordinate names (e.g., latitude)

    # Find specific dataset name for each coordinate for time, lat and lon
    time_name = [v for v in coord_names if 'time'.casefold() in v.casefold()][0]
    lat_name  = [v for v in coord_names if 'lat'.casefold() in v.casefold()][0]
    lon_name  = [v for v in coord_names if 'lon'.casefold() in v.casefold()][0]

    # Return dictionary mapping dataset specific 
    # coordinate names to predefined terms.
    name_dict = {'time': time_name,'lat': lat_name,'lon': lon_name}

    return name_dict    

def extract_str_parts(filelist,extension='',sep='_'):

    n_files = len(filelist)
    n_filename_parts = len(os.path.split(filelist[0])[1].split(sep))

    filename_parts = np.zeros((n_files,n_filename_parts),dtype=object)

    for i in range(n_files):

        file_i = os.path.split(filelist[i])[1].split('.' + extension)[0]
        filename_parts_i = file_i.split(sep)
        
        filename_parts[i,] = filename_parts_i
    
    return filename_parts

def get_geoaxes(ds,coord_axes=None):

    if coord_axes is None:

        try:
            axes = ds.cf.axes
            axes['X']
            axes['Y']
        except:
            axes = {'X': ['lon'],'Y': ['lat']}

    return axes

def get_geocoords(coords,**kwargs):

    """    
    coords: 
        Can be in one of the following formats:
            1. a string to a file location that has the spatial coordinates 
            needed for interpolation
            2. An xarray dataset or dataarray with assigned coordinates
            3. It can be a tuple of length 2, with each tuple element 
            comprising either a list of x,y values or a numpy array of x,y 
            values. Tuple order must be x,y.

    coord_axes: 
        If supplied, must be a dict mapping the coordinate names to the
        'X' and 'Y' axes. If not suppled, cf_xarray axes is used to determine 
        the mapping between axes and coordinates.

        e.g., coord_axes = {'X': 'lon','Y': 'lat'}   
    """ 

    if not isinstance(coords,tuple):

        if isinstance(coords,pathlib.PosixPath) or isinstance(coords,str):

            ds_for_coords = xr.load_dataset(coords)

        elif isinstance(coords,xr.DataArray) | isinstance(coords,xr.Dataset):

            ds_for_coords = coords

        axes = get_geoaxes(ds_for_coords,**kwargs)

        x = ds_for_coords[axes['X'][0]].values
        y = ds_for_coords[axes['Y'][0]].values

    else:

        x, y = coords

    return (x,y)

def coords_to_mesh(coords,flatten=False,**kwargs):

    """
    flatten: bool
        False will return 2d array and True will return 1D array    
    """

    x,y = get_geocoords(coords,**kwargs)

    X,Y = np.meshgrid(x,y,indexing='xy')

    if flatten:
        X = X.flatten()
        Y = Y.flatten()

    return (X,Y)    

def regrid_geodata(ds,target_coords,method='linear',**kwargs):

    # Get axes for current xarray dataset. Will return empty dict if not 
    # available
    axes = get_geoaxes(ds)

    # Get x and y coordinate values
    x,y = get_geocoords(target_coords,**kwargs)

    # Use built in xarray interp function to do interpolation
    ds_interp = ds.interp({
        axes['X'][0]: x,
        axes['Y'][0]: y
        },
        method=method)

    return ds_interp

def mask_from_shp(shpfile,grd_coords,**kwargs):

    if isinstance(shpfile,pathlib.PosixPath) or isinstance(shpfile,str):

        mask_vct = gpd.read_file(shpfile)

    else: 

        mask_vct = shpfile

    x,y = coords_to_mesh(grd_coords,**kwargs)

    mask_geom = mask_vct.dissolve().geometry.item()

    mask_grd = shapely.vectorized.contains(mask_geom,x,y)

    return mask_grd