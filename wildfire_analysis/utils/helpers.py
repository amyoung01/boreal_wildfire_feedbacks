"""
Description
-----------
This is set of utility and helper functions to accompany this analysis. Most of
these functions are shortcuts to extracting and processing relevant data from 
xarray objects.
"""

import datetime as dt
import os
import pathlib
from typing import Iterable
# from keyword import kwlist 

import geopandas as gpd
import numpy as np
import shapely.vectorized
import rasterio as rio
import xarray as xr

def get_root_dir() -> str:

    """
    Description
    -----------
    Get root directory of package module for current project.

    Parameters
    ----------
    None

    Returns
    -------
    str
        A string specifying the full path of the root directory.
    """      

    return str((pathlib.Path(__file__).parent / '../').resolve())

def get_kwargs(x: dict,kwargs: Iterable) -> dict:

    """
    Description
    -----------
    Allows user to pass a dictionary of kwargs for multiple functions. This 
    Function searches the kwarg dict and finds those only needed for a specific
    function.

    Parameters
    ----------
    x: dict
        A dictionary of kwargs for multiple functions
    kwargs: Iterable
        Sequence of kwargs needed for specific function.

    Returns
    -------
    dict
        Dictionary of kwargs for specific function to be passed.
    """
    
    return {k:kwargs[k] for k in x if k in kwargs}

def get_var_names(ds: xr.Dataset) -> list:

    """
    Description
    -----------
    Get variable names from xarray dataset.
    """

    # Return list of all variable names in netcdf dataset
    return list(ds.keys())

def trim_geolims(ds: xr.Dataset,geolims: Iterable) -> xr.Dataset:

    """
    Description
    -----------    
    Clip geographic extent of xarray dataset. Assumes X and Y axes are 'lat' 
    and 'lon'.

    Parameters
    ----------
    ds: xarray.Dataset
        Dataset to clip
    geolims: Iterable
        Iterable to coordinates to define new extent of geographic limits: \
        (left, bottom, right, top)

    Returns
    -------
    ds: xarray.Dataset
        Dataset with new geographic extent
    """

    coord_names = get_coord_names(ds)

    lonlim = (geolims[0],geolims[2])
    latlim = (geolims[1],geolims[3])

    ds = ds.sortby(coord_names['lat'])

    sel_dict = {coord_names['lat']: slice(latlim[0],latlim[1]),
                coord_names['lon']: slice(lonlim[0],lonlim[1])}
    
    ds = ds.loc[sel_dict]

    return ds

def get_coord_names(ds) -> dict:

    """
    Description
    -----------
    Returns dictionary of coordinate names from an xarray datast. Assumes
    it is geographically projected and that there are three dimensions 
    (time, lat, lon).
    """

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

def get_axes_names(ds) -> dict:

    """
    Description
    -----------    
    Get coordinate variable names for each specific dimension (X, Y, and T) in
    an xarray dataset.
    """

    coord_names = get_coord_names(ds)

    axes_dict = {}

    for name in coord_names:

        axis = ds[name].attrs['axis']

        axes_dict.update({axis: name})

    return axes_dict

def extract_str_parts(filelist: list,
                      extension: str='',
                      sep: str='_') -> np.ndarray:

    """
    Description
    -----------    
    Parse filenmaes by separation string to return individual filename parts.

    Parameters
    ----------
    filelist: list
        List of filnames to separate
    extension: str
        Extension of file to remove (if desired)
    sep: str
        Character to separate and split filenames

    Returns
    -------
    numpy.ndarray
        Array of filename parts
    """    

    n_files = len(filelist)
    n_filename_parts = len(os.path.split(filelist[0])[1].split(sep))

    filename_parts = np.zeros((n_files,n_filename_parts),dtype=object)

    for i in range(n_files):

        file_i = os.path.split(filelist[i])[1].split('.' + extension)[0]
        filename_parts_i = file_i.split(sep)
        
        filename_parts[i,] = filename_parts_i
    
    return filename_parts

def get_geoaxes(ds: xr.Dataset,coord_axes=None) -> dict:

    """
    Description
    -----------    
    Get geographic axes names for X and Y dimensions/coordinates.
    """
    if coord_axes is None:

        try:
            axes = get_axes_names(ds)
            axes['X']
            axes['Y']
        except:
            axes = {'X': ['lon'],'Y': ['lat']}

    return axes

def get_geocoords(coords,**kwargs) -> tuple:

    """
    Description
    -----------
    Get geographic coordinates (x,y) values from xarray dataset

    Parameters
    ----------  
    coords: str, pathlib.Path, xarray.Dataset, xarray.DataArray, tuple
            (str or pathlib.Path) file location that has the spatial 
            coordinates needed for interpolation, (xarray.Dataset or
            xarray.DataArray) with desired coordinates, (tuple) tuple of length 
            2, with each tuple element comprising either a list of x,y values 
            or a numpy.ndarray of x,y values. Tuple order must be x,y.
    coord_axes: dict
        If supplied, must be a dict mapping the coordinate names to the
        'X' and 'Y' axes. If not suppled, cf_xarray axes is used to determine 
        the mapping between axes and coordinates.

        e.g., coord_axes = {'X': 'lon','Y': 'lat'}
    
    Returns
    -------
    tuple
        x,y coordinates of dataset
    """ 

    if not isinstance(coords,tuple):

        if isinstance(coords,pathlib.Path) or isinstance(coords,str):

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
    Description
    -----------
    Returns numpy meshgrid for a given set of coordinate values in 2 dimensions

    Parameters
    ----------
    coords
        x,y coordinates or xarray.Dataset that contains desired geographic
        coordinates
    flatten: bool
        False will return 2d array and True will return 1D array

    Returns
    -------
    tuple of numpy.ndarrays
        (X,Y) with X and Y as numpy.ndarrays
    """

    x,y = get_geocoords(coords,**kwargs)

    X,Y = np.meshgrid(x,y,indexing='xy')

    if flatten:
        X = X.flatten()
        Y = Y.flatten()

    return (X,Y)    

def regrid_geodata(ds: xr.Dataset,
                   target_coords,
                   method='linear',
                   **kwargs) -> xr.Dataset:

    """
    Shortcut to using xarrays built in interpolation function.
    """

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

def raster_transform_to_coords(rst_file) -> tuple:

    """
    Description
    -----------
    Use rasterio library to get x and y coordinate values for a raster dataset

    Parameters
    ----------
    rst_file: str or pathlib.Path
        File location of raster dataset

    Returns
    -------
    tuple
        Tuple of geographic coordinates for raster dataset
    """

    with rio.open(rst_file) as ds:
        transform = ds.get_transform()
        height, width = ds.shape

    origin = (transform[0],transform[3])
    res = (transform[1],transform[5])
    size = (width,height)    

    n = len(origin)

    coords = ()

    for i in range(n):

        coords_i = np.arange(origin[i]+res[i]/2,
                             origin[i]+res[i]/2 + size[i]*res[i],
                             res[i])
        
        coords = coords + (coords_i,)

    return coords

def mask_from_shp(shpfile: gpd.GeoDataFrame,grd_coords,**kwargs) -> np.ndarray:

    """
    Description
    -----------
    Use rasterio library to get x and y coordinate values for a raster dataset

    Parameters
    ----------
    shpfile: str, pathlib.Path, geopandas.GeoDataFrame
        File location of ESRI Shapefile or geopandas.GeoDataFrame
    grd_coords: 
        File, xarray.Dataset, or tuple(x,y) containing coordinates to mask with
        shpfile

    Returns
    -------
    numpy.ndarray
        numpy array of dtype=bool of spatial mask defined by shpfile
    """    

    # Get gridded geospatial mask for a region covered by an ESRI shapefile

    if isinstance(shpfile,pathlib.Path) or isinstance(shpfile,str):

        mask_vct = gpd.read_file(shpfile)

    else: 

        mask_vct = shpfile

    x,y = coords_to_mesh(grd_coords,**kwargs)

    mask_geom = mask_vct.dissolve().geometry.item()

    mask_grd = shapely.vectorized.contains(mask_geom,x,y)

    return mask_grd