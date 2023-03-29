#!/usr/bin/env python3

#%% Import libraries
from itertools import product
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio as rio
import xarray as xr
import yaml
from pyproj import CRS

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

#%% Import config file and read in parameters needed for data processing
# Get global values from configuration file
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:   
    config_params = yaml.safe_load(config_file)

    processed_data_dir = root_dir / config_params['PATHS']['processed_data_dir']
    dataframes_dir = root_dir / config_params['PATHS']['dataframes_data_dir']
    fire_yr =config_params['TIME']['fire_yr'] 
    hst_yr = config_params['TIME']['era5_yr']
    crs = CRS.from_wkt(config_params['CRS'])

#%% Import ecoregion shapefile
ecos_fn = processed_data_dir / 'ecoregions/ecos.shp'
ecos = gpd.read_file(ecos_fn)
eco_id = ecos['ECO_ID']

#%% Set directory of location for fire geotiff files that provide pres/abs for 
# fire at 1-km resolution for each year
fire_rst_dir = processed_data_dir / 'fire/rasters'
fire_yr = range(fire_yr[0],fire_yr[1]+1)

for yr in fire_yr:

    fn  = list(fire_rst_dir.glob('*%d.tif' % yr))[0]

    with rio.open(fn) as ds:
        fire_y = ds.read(1)

    # To concatenate along 0 axis for time
    fire_y = fire_y[np.newaxis,...]

    if 'fire_stack' not in locals():
        
        fire_stack = fire_y.copy()        

        del fire_y        
        
        continue

    fire_stack = np.concatenate((fire_stack,fire_y),axis=0)

    del fire_y

# Get x and y coordinate values for fire dataset
coords = h.raster_transform_to_coords(fn)

#%% Summarize annual area burned for each ecoregion for each year
for id in eco_id:

    ecos_i = ecos.loc[ecos['ECO_ID']==id,:]
    ecos_i = ecos_i.to_crs(crs) # Reproject to Albers Equal Area projection

    mask = h.mask_from_shp(ecos_i,coords)
    mask_Nd = np.broadcast_to(mask,fire_stack.shape)
    mask_Nd = mask_Nd.astype('int')

    fire_stack_i = fire_stack * mask_Nd

    # sum all sparial values for each year
    fire_sums_i = np.sum(fire_stack_i,axis=(1,2)) 

    aab_df_i = pd.DataFrame()
    aab_df_i['year'] = fire_yr
    aab_df_i['ecos'] = id
    aab_df_i['annual_area_burned_km2'] = fire_sums_i

    if 'aab_df' not in locals():            
        aab_df = aab_df_i.copy()        
    else:
        aab_df = pd.concat([aab_df,aab_df_i])

    del aab_df_i

export_fn = dataframes_dir / 'observed_area_burned.csv'
aab_df.to_csv(export_fn,index=False)
