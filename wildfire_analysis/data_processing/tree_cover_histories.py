"""
Description
-----------
This script will go through each individual fire perimeter (> 200 ha) from the 
Alaskan Large Fire Database and Canadian National Fire Database from 1950-2015
and get an estimate of the mean tree cover for the years 2001-2020. This 
function only looks at the treecover data for the regions of the fire perimeter
that have no record of subsequent burning after the fire event. It clips out
areas that did have reburns. The final product is a CSV table that provides
an estimate of treecover as a function of time since fire for all fire 
patches that had no reburning.
"""

# Import required libraries
import yaml
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio as rio
from rasterio.mask import mask
from shapely.geometry import mapping
from tqdm import tqdm

from wildfire_analysis.utils import helpers as h

# Suppress warnings. Upon inspection none of these warnings indicated our 
# results were NOT being processed correctly.
import warnings
warnings.filterwarnings('ignore',
                        message='invalid value encountered in difference')
warnings.filterwarnings('ignore',
                        message='invalid value encountered in intersection')
warnings.filterwarnings('ignore',
                        message='invalid value encountered in unary_union')
warnings.filterwarnings('ignore',
                        message='FutureWarning: In a future version, `df.iloc[:, i] = newvals` will attempt to set the values inplace instead of always setting a new array. To retain the old behavior, use either `df[df.columns[i]] = newvals` or, if columns are non-unique, `df.isetitem(i, newvals)` df.loc[mask, col] = df.loc[mask, col].buffer(0)')

# Set verbose to True to print out progress bar
verbose = True

# Import config file and read in parameters needed for data processing
# Get global values from configuration file
root_dir = Path(h.get_root_dir())
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:
    config_params = yaml.safe_load(config_file)

    data_dir = root_dir / config_params['PATHS']['processed_data_dir']
    fire_yr = config_params['TIME']['fire_yr']
    treecov_yr = config_params['TIME']['treecov_yr']

# Create ranges for fire years and mod44b years
fire_yr = range(fire_yr[0],fire_yr[1]+1)
treecov_yr = range(treecov_yr[0],treecov_yr[1]+1)

# Read in projected ecoregions shapefile
fn = data_dir / 'ecoregions/ecos_reproj.shp'
ecos = gpd.read_file(fn)

# Read in fire history shapefile
fn = data_dir / 'fire/shapefiles/AK_Canada_large_fire_history.shp'
firehx_shp = gpd.read_file(fn)
firehx_shp = firehx_shp.sort_values(by='FIREYR')
firehx_shp = firehx_shp.reset_index(drop=True)

# Record fire years and fire size as numpy array objects
fire_yr = firehx_shp.FIREYR.values
fire_size = firehx_shp.HECTARES.values

# Set up empty dictionary to record results
export_dict = {"fire_yr": [],
            "ecos": [],
            "area_burned_km2": [],
            "time_of_last_fire": [],
            "tree_cover_mean": []}

# Total number of fire permiters to process
N = firehx_shp.shape[0]

with tqdm(total=N,disable=not verbose) as pbar:

    for i in range(0,N):

        # Subset ith shapefile
        fire_i = firehx_shp.iloc[[i],:]

        # Determine what ecoregion the current fire perimeter is in
        ecos_overlap = fire_i.overlay(ecos,how="intersection")

        if ecos_overlap.shape[0] == 0:

            ecos_id = None

        elif ecos_overlap.shape[0] == 1:

            ecos_id = ecos_overlap.at[0,"ECO_ID"]

        elif ecos_overlap.shape[0] > 1:

            overlap_area = ecos_overlap.area.values
            max_overlap = np.flatnonzero(overlap_area == max(overlap_area))[0]

            ecos_id = ecos_overlap.at[max_overlap,"ECO_ID"]

        if (ecos_id is None):

            pbar.update()

            continue

        # Subset fire history dataset to find all fires that occur after the 
        # ith one
        out_id = fire_yr > fire_yr[i]
        fire_subset_i = firehx_shp.loc[out_id]

        # Further subset to find all fire perimeters that occurred near ith one
        spatial_index = fire_subset_i.sindex
        bounds = tuple(fire_i.bounds.values[0])
        out_id = list(spatial_index.intersection(bounds))
        fire_subset_i = fire_subset_i.iloc[out_id].dissolve()

        # Find all geometries within current fire perimeter that have not 
        # experienced any documented reburning after it occurred
        fire_i_noreburn = fire_i.overlay(fire_subset_i,how="difference")

        if fire_i_noreburn.shape[0] == 0:

            pbar.update()

            continue

        # Convert area burned values of no reburing geometrie(s) to km^2
        area_burned = np.round(fire_i_noreburn.area.values[0] * 1e-6,2)

        # Get geometries and put into list
        geoms = fire_i_noreburn.geometry.values
        geoms = [mapping(geoms[0])]

        # Go through each year we have modis tree cover data for and record 
        # what the mean treecover is for each year after the fire occurred
        postfire_yr_id = np.flatnonzero(treecov_yr >= fire_yr[i] - 1)

        for j in postfire_yr_id:

            export_dict["fire_yr"].append(fire_yr[i])
            export_dict["ecos"].append(ecos_id)
            export_dict["time_of_last_fire"].append(
                0 - (treecov_yr[j] - fire_yr[i])
                )
            export_dict["area_burned_km2"].append(area_burned)

            mod44b_path = root_dir / '../data/processed/veg/mod44b'
            fn = list(mod44b_path.glob('*Tree_Cover*%d*' % treecov_yr[j]))[0]
                            
            treecov_j = rio.open(fn)
            treecov_image, _ = mask(treecov_j,geoms,crop=True)
            treecov_image = treecov_image.astype("float32")

            treecov_values = treecov_image[(treecov_image >= 0) 
                                           & (treecov_image <= 100)]

            if treecov_values.size == 0.0:

                export_dict["tree_cover_mean"].append(np.nan)

            else:

                export_dict["tree_cover_mean"].append(
                    np.nanmean(treecov_values)
                    )

        pbar.update() # Update progress bar

# Export recorded time since fire and tree cover values into csv file
export_df = pd.DataFrame.from_dict(export_dict)
export_fn = root_dir / '../data/dataframes/modis_treecover_postfire.csv'
export_df.to_csv(export_fn, index=False)

# Don't automatically run when imported into another script
if __name__ == '__main__':

    None