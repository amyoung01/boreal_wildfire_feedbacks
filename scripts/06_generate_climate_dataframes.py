from itertools import product
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
import yaml

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

# Import config file and read in parameters needed for data processing
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

ecos_fn = root_dir / '../data/ancillary/ecos.shp'
ecos = gpd.read_file(ecos_fn)
eco_id = ecos['ECO_ID']

cffdrs_stats_dir = root_dir / '../data/processed/cffdrs/cffdrs_stats'

src_to_process = ['era5'] + gcm_list

for src in src_to_process:

    fn = list(cffdrs_stats_dir.glob('*%s*' % src))[0]
    ds = xr.load_dataset(fn,engine='h5netcdf')
    arr_shape = ds['fwi'].shape

    for id in eco_id:

        mask = h.mask_from_shp(ecos.loc[ecos['ECO_ID']==id,:],ds)
        mask_Nd = np.broadcast_to(mask,arr_shape)
        ds_ecos_i = ds.where(mask_Nd)

        fw_avgs_ds = ds_ecos_i.mean(dim=['lat','lon'])
        fw_avgs_df_i = pd.DataFrame()
        fw_avgs_df_i['year'] = fw_avgs_ds['year'].values
        fw_avgs_df_i['ecos'] = id
     
        vars = h.get_var_names(fw_avgs_ds)
        stats_ = list(fw_avgs_ds['stat'].values)

        for x, y in product(vars, stats_):
            fw_avgs_df_i['_'.join([x,y])] = fw_avgs_ds[x].sel(stat=y).values

        if 'fw_avgs_df' not in locals():            
            fw_avgs_df = fw_avgs_df_i.copy()            
        else:
            fw_avgs_df = pd.concat([fw_avgs_df,fw_avgs_df_i])

        del fw_avgs_ds, fw_avgs_df_i

    yr = fw_avgs_df['year'].unique()
        
    df_fn = dataframes_dir / ('cffdrs-stats_%s_%d-%d.csv' % (src,yr[0],yr[-1]))
    fw_avgs_df.to_csv(df_fn,index=False)

    del fw_avgs_df