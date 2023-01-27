from pathlib import Path

root_dir = Path(__file__).parent

data_dir = Path(root_dir / '../data').resolve()

ancillary_data_dir = data_dir / 'ancillary'
raw_data_dir = data_dir / 'raw'
processed_data_dir = data_dir / 'processed'
dataframes_data_dir = data_dir / 'dataframes'
model_results_data_dir = data_dir / 'model_results'

geo_lims = [-177.1875,35.0,-35.0,79.375]

gcm_list = [
    'ACCESS-CM2',
    'CNRM-CM6-1-HR',
    'EC-Earth3-Veg',
    'MPI-ESM1-2-HR',
    'MRI-ESM2-0'
    ]

metvars = [
    'tasmax',
    'pr',
    'sfcWind',
    'hursmin'
    ]

fire_yr = [1950,2020]
treecov_yr = [2001,2020]
era5_yr = [1979,2020]
cmip6_yr = [1979,2099]
hst_yr = [1980,2009]
sim_periods = ([2010,2039],[2040,2069],[2070,2099])


# Values needed for quantile delta mapping
oper = {
    'tasmax': '+',
    'pr': '*',
    'sfcWind': '*',
    'hursmin': '*'
    }

min_thresh = {
    'tasmax': None,
    'pr': 0.5,
    'sfcWind': None,
    'hursmin': None
    }

quantile_vals = [0.005] + [x/100 for x in range(1,100)] + [0.995]