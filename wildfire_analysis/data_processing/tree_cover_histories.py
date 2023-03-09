import yaml
from io import StringIO
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio as rio
from rasterio.mask import mask
from shapely.geometry import mapping
from tqdm import tqdm

from wildfire_analysis.utils import helpers as h

import warnings
warnings.filterwarnings('ignore',
                        message='invalid value encountered in difference')
warnings.filterwarnings('ignore',
                        message='invalid value encountered in intersection')
warnings.filterwarnings('ignore',
                        message='invalid value encountered in unary_union')

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


fire_yr = range(fire_yr[0],fire_yr[1]+1)
treecov_yr = range(treecov_yr[0],treecov_yr[1]+1)

fn = data_dir / 'ecoregions/ecos_reproj.shp'
ecos = gpd.read_file(fn)

fn = data_dir / 'fire/shapefiles/AK_Canada_large_fire_history.shp'
firehx_shp = gpd.read_file(fn)
firehx_shp = firehx_shp.sort_values(by='FIREYR')
firehx_shp = firehx_shp.reset_index(drop=True)

fire_yr = firehx_shp.FIREYR.values
fire_size = firehx_shp.HECTARES.values

export_dict = {"fire_yr": [],
            "ecos": [],
            "area_burned_km2": [],
            "time_since_fire": [],
            "tree_cover_mean": []}

N = firehx_shp.shape[0]

with tqdm(total=N,disable=not verbose) as pbar:

    for i in range(0,N):

        fire_i = firehx_shp.iloc[[i],:]

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

        out_id = fire_yr > fire_yr[i]
        fire_subset_i = firehx_shp.loc[out_id]

        spatial_index = fire_subset_i.sindex
        bounds = tuple(fire_i.bounds.values[0])
        out_id = list(spatial_index.intersection(bounds))
        fire_subset_i = fire_subset_i.iloc[out_id].dissolve()

        fire_i_noreburn = fire_i.overlay(fire_subset_i,how="difference")

        if fire_i_noreburn.shape[0] == 0:

            pbar.update()

            continue

        area_burned = np.round(fire_i_noreburn.area.values[0] * 1e-6,2)

        geoms = fire_i_noreburn.geometry.values
        geoms = [mapping(geoms[0])]

        postfire_yr_id = np.flatnonzero(treecov_yr >= fire_yr[i] - 1)

        for j in postfire_yr_id:

            export_dict["fire_yr"].append(fire_yr[i])
            export_dict["ecos"].append(ecos_id)
            export_dict["time_since_fire"].append(treecov_yr[j] - fire_yr[i])
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

                export_dict["tree_cover_mean"].append(np.nanmean(treecov_values))

        pbar.update()

export_df = pd.DataFrame.from_dict(export_dict)
export_fn = root_dir / '../data/dataframes/treecov_postfire.csv'
export_df.to_csv(export_fn, index=False)