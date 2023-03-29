#!/usr/bin/env python3

#%% Import libraries
import itertools
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
import yaml

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

#%% Import config file and read in parameters needed for data processing
# Get global values from configuration file
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:   
    config_params = yaml.safe_load(config_file)

    processed_data_dir = root_dir / config_params['PATHS']['processed_data_dir']
    dataframes_dir = root_dir / config_params['PATHS']['dataframes_data_dir']
    gcm_list = config_params['CLIMATE']['gcm_list']
    era5_yr = config_params['TIME']['era5_yr']
    hst_yr = config_params['TIME']['hst_yr']
    sim_periods = config_params['TIME']['sim_periods']

#%% Import ecoregion shapefile
ecos_fn = processed_data_dir / 'ecoregions/ecos.shp'
ecos = gpd.read_file(ecos_fn)
ecos_id = ecos['ECO_ID']

#%% Set directory for CFFDRS statistical summaries
cffdrs_stats_dir = processed_data_dir / 'cffdrs/cffdrs_stats'

#%% Set list of sources to process, including all GCMs and ERA5
src_to_process = ['era5'] + gcm_list

#%% For each sources get spatial average of each statistical summary and export

fw_df = pd.DataFrame()

for src in src_to_process:

    fn = list(cffdrs_stats_dir.glob('*%s*' % src))[0]
    ds = xr.load_dataset(fn,engine='h5netcdf')
    ds = ds.transpose('stat','year','lat','lon')
    arr_shape = ds['fwi'].shape
        
    for id in ecos_id:

        mask = h.mask_from_shp(ecos.loc[ecos['ECO_ID']==id,:],ds)
        mask_Nd = np.broadcast_to(mask,arr_shape)
        ds_ecos_i = ds.where(mask_Nd)

        fw_avgs = ds_ecos_i.mean(dim=['lat','lon'])

        yr = ds['year'].values.tolist()
        stats_ = ds['stat'].values.tolist()
        vars = h.get_var_names(fw_avgs)

        data = {
            'ecos': id,
            'year': fw_avgs['year'].values,
            'source': src,
        }

        for v1, v2 in itertools.product(vars,stats_):

            data.update(
                {"_".join([v1,v2]): fw_avgs[v1].sel(stat=v2).values.tolist()}
                )

        fw_df = pd.concat((fw_df,pd.DataFrame(data)),axis=0)

fw_df = fw_df.round(3)

fn = dataframes_dir / 'cffdrs_annual_stats.csv'

commented_lines = ['# cffdrs_annual_stats.csv\n',
                   '# Annual summary statistics for ISI BUI and FWI for each ecoregion\n',
                   '# Columns descriptions:\n',
                   '# \t ecos: ecoregion\n',
                   '# \t source: ERA5 or one of the GCMs\n',
                   '# \t isi_max: Maximum initial spread index anomaly relative to 1980-2009 \n',
                   '# \t isi_95d: Number of days that exceeds historical 95th percentile of initial spread index\n',
                   '# \t isi_fs: Maximum 90-day moving window of initial spread index\n',
                   '# \t isi_fwsl: Number of days that exceed the historial midpoint of the range historical initial spread index relative to 1980-2009\n',
                   '# \t bui_max: Maximum build up index anomaly relative to 1980-2009\n',
                   '# \t bui_95d: Number of days that exceeds historical 95th percentile of build up index\n',
                   '# \t bui_fs: Maximum 90-day moving window of build up index\n',
                   '# \t bui_fwsl: Number of days that exceed the historial midpoint of the range historical build up index relative to 1980-2009\n',
                   '# \t fwi_max: Maximum fire weather index anomaly relative to 1980-2009\n',
                   '# \t fwi_95d: Number of days that exceeds historical 95th percentile of fire weather index\n',
                   '# \t fwi_fs: Maximum 90-day moving window of fire weather index\n',
                   '# \t fwi_fwsl: Number of days that exceed the historial midpoint of the range historical fire weather index relative to 1980-2009\n',
                   '#\n']

with open(fn, 'w') as f:
    f.write("".join(commented_lines))

fw_df.to_csv(fn, mode='a', index=False)
