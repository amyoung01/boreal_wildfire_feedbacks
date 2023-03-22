# Import required libraries
import itertools
import yaml
from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np
from tqdm import tqdm as tqdm
import xarray as xr

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

def get_monthly_averages(da,mask_grid=None):
   
    if mask_grid is not None:
        x = da.where(mask_grid)
    else:
        x = da
    y = x.groupby('time.month').mean(dim=['lat','lon','time'])

    return y

ecos = gpd.read_file(root_dir / '../data/processed/ecoregions/ecos.shp')
ecos_id = ecos.ECO_ID

config_fn = root_dir / 'config.yaml'

with open(config_fn, 'r') as config_fn:
    config_params = yaml.safe_load(config_fn)

    metvars = config_params['CLIMATE']['metvars']
    gcm_list = config_params['CLIMATE']['gcm_list']

years = range(1980,2099+1)

months = range(1,12+1)

sources = ['era5'] + gcm_list

cffdrs_vars = ['ffmc', 'dmc', 'dc', 'isi', 'bui', 'fwi']
vars = metvars + cffdrs_vars

col_labels = ['source', 'ecos', 'year', 'month'] + vars

era5_dir = root_dir / '../data/processed/climate/era5'
cmip6_dir = \
    [(root_dir / '../data/processed/climate/cmip6').joinpath(d,'bias_corrected') \
        for d in gcm_list]
era5_cffdrs_dir = root_dir / '../data/processed/cffdrs/era5'
cmip6_cffdrs_dir = \
    [(root_dir / '../data/processed/cffdrs/cmip6').joinpath(d) \
        for d in gcm_list]

dirs = [era5_dir] + cmip6_dir + [era5_cffdrs_dir] + cmip6_cffdrs_dir

n = len(years) * len(ecos_id) * len(sources) * len(months)
init_array = -9999.0 * np.ones((n,len(col_labels)))

export_df = pd.DataFrame(init_array,columns=col_labels)

_count = 0

for v1, v2, v3, v4 in itertools.product(years,ecos_id,sources, months):

    id = export_df.index == _count

    export_df.loc[id,'year'] = v1
    export_df.loc[id,'ecos'] = v2
    export_df.loc[id,'source'] = v3
    export_df.loc[id,'month'] = v4

    _count += 1

export_df = export_df.sort_values(by=['source','ecos','year','month'])
export_df = export_df.reset_index(drop=True)
export_df = export_df.astype({'year': 'int', 'month': 'int'})

niter = np.sum(np.array([len(list(d.glob('*.nc'))) for d in dirs]))

with tqdm(total=niter) as pbar: # for progress bar

    for d in dirs:

        files = list(d.glob('*.nc'))
        files.sort()

        for f in files:

            ds = xr.load_dataset(f,engine='h5netcdf')
            ds = ds.transpose('time','lat','lon')

            f = f.name
            fileparts = f.split('_')
            variable = fileparts[0]
            src = fileparts[1]
            yr = int(fileparts[2][:-3])

            if yr not in years:
                continue

            for e in ecos_id:

                # Subset shapefile to current ecoregion
                ecos_i = ecos.loc[ecos['ECO_ID'] == e]

                mask_grd = h.mask_from_shp(ecos_i,ds)
                mask_grd = np.repeat(mask_grd[np.newaxis,...],
                                        ds['time'].size, 
                                        axis = 0)

                x = get_monthly_averages(ds,mask_grid=mask_grd)

                var_names = h.get_var_names(x)
                mon = x['month'].values

                for v1, v2 in itertools.product(var_names,mon):

                    id = (export_df['year'] == yr) \
                        & (export_df['ecos'] == e) \
                        & (export_df['source'] == src) \
                        & (export_df['month'] == v2)
                    
                    export_df.loc[id,v1] = x[v1].sel(month=v2).values

            pbar.update()

# Rounfd all area burned results to one decimal place
export_df = export_df.round(3)

# Add header with metadata to csv file that is exported
fn = root_dir / '../data/dataframes/monthly_weather_summaries.csv'
commented_lines = ['# monthly_weather_summaries.csv\n',
                   '# Monthly averages of meteorological and fire weather metrics for each ecoregion\n'
                   '# -9999 = NoData\n',
                   '# Columns descriptions:\n',
                   '# \t ecos: ecoregion\n',
                   '# \t source: ERA5 or one of the GCMs\n',
                   '# \t tasmax: average daily maximum temperature in degrees Celsius\n',
                   '# \t pr: average daily total precip in mm/day\n',
                   '# \t sfcWind: average daily mean wind speed in km/hour\n',
                   '# \t hursmin: average daily minimum relative humidity in %\n',
                   '# \t ffmc: average daily fine fuel moisture code\n',
                   '# \t dmc: average daily duff moisture code\n',
                   '# \t dc: average daily drought code\n',
                   '# \t isi: average daily initial spread index\n',
                   '# \t bui: average daily build up index\n',
                   '# \t fwi: average daily fire weather index\n',
                   '#\n']

with open(fn, 'w') as f:
    f.write("".join(commented_lines))

export_df.to_csv(fn, mode='a', index=False)
