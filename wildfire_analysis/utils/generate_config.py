from pathlib import Path

import yaml

root_dir = Path(__file__).parents[1]

paths = dict(
    data_dir='../data',
    ancillary_data_dir='../data/ancillary',
    raw_data_dir='../data/raw',
    processed_data_dir= '../data/processed',
    dataframes_data_dir='../data/dataframes',
    model_results_data_dir='../data/model_results',
    )

climate_params = dict(
    geo_lims=[-177.1875,35.0,-35.0,79.375],
    gcm_list=['EC-Earth3-Veg','MPI-ESM1-2-HR','MRI-ESM2-0','CNRM-CM6-1-HR'],
    metvars=['tasmax','pr','sfcWind','hursmin'],
    )

# Time spans for different variables/datasets, needed for processing
time_spans = dict(
    fire_yr=[1950,2020],
    treecov_yr=[2001,2020],
    era5_yr=[1979,2020],
    cmip6_yr=[1979,2099],
    hst_yr=[1980,2009],
    sim_periods=[[2010,2039],[2040,2069],[2070,2099]],
    )

# Values needed for quantile delta mapping
qdm_params = dict(
    oper={'tasmax': '+','pr': '*','sfcWind': '*','hursmin': '*'},
    min_thresh={'tasmax': None,'pr': 0.5,'sfcWind': None,'hursmin': None},
    quantile_vals=[0.005] + [x/100 for x in range(1,100)] + [0.995],
    )

config_dict = dict(
    PATHS=paths,
    CLIMATE=climate_params,
    TIME=time_spans,
    QDM=qdm_params,
    )

config_filename = root_dir / 'config.yaml'
with open(config_filename, 'w') as config_file:
    yaml.safe_dump(
        config_dict,
        config_file,
        default_flow_style=False,
        sort_keys=False,
        )