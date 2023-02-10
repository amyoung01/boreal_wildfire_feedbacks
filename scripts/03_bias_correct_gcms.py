#!/usr/bin/env python3

#%% Import libraries
from pathlib import Path
import sys

import numpy as np
from tqdm import tqdm
import yaml

from wildfire_analysis.data_processing.quantile_delta_mapping \
    import quantile_delta_mapping
from wildfire_analysis.utils import helpers as h

#%% Import config file and read in parameters needed for data processing
# Get global values from configuration file
root_dir = Path(h.get_root_dir())
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:

    config_params = yaml.safe_load(config_file)

    ancillary_data_dir = root_dir / config_params['PATHS']['ancillary_data_dir']
    processed_data_dir = root_dir / config_params['PATHS']['processed_data_dir']
    gcm_list = config_params['CLIMATE']['gcm_list']
    metvars = config_params['CLIMATE']['metvars']
    hst_yr = config_params['TIME']['hst_yr']
    sim_periods = config_params['TIME']['sim_periods']
    oper = config_params['QDM']['oper']
    min_thresh = config_params['QDM']['min_thresh']
    quantile_vals = config_params['QDM']['quantile_vals']

#%% If verbose=True then have progress bar document processing time
verbose = False
if sys.argv[-1] == '--verbose':
    verbose = True

shpfile = ancillary_data_dir / 'ecos.shp'

refdir = processed_data_dir / 'climate/era5'

quantile_vals = np.array(quantile_vals)

N = len(gcm_list)*len(metvars)*len(sim_periods)

with tqdm(total=N,disable=not verbose) as pbar: # for progress bar

    for gcm in gcm_list:

        wdir = processed_data_dir / 'climate/cmip6' / gcm
        dest = processed_data_dir / 'climate/cmip6' / gcm / 'bias_corrected'

        if dest.exists() is False:
            dest.mkdir(parents=True)
        
        for var in metvars:

            for sim_yr in sim_periods:
                
                ref_src = [list(refdir.glob("%s*%d*" % (var,i)))[0] \
                    for i in range(hst_yr[0],hst_yr[1]+1)]

                hst_src = [list(wdir.glob("%s*%d*" % (var,i)))[0] \
                    for i in range(hst_yr[0],hst_yr[1]+1)]

                sim_src = [list(wdir.glob("%s*%d*" % (var,i)))[0] \
                    for i in range(sim_yr[0],sim_yr[1]+1)]

                if sim_yr == sim_periods[0]:
                    hst_return_bool = True
                else:
                    hst_return_bool = False

                qdm = quantile_delta_mapping(
                    ref_src,hst_src,sim_src,
                    dask_load=True,
                    regrid='gcm2era',
                    mask=shpfile,
                    kind=oper[var],
                    nquantiles=quantile_vals,
                    group='time.month',
                    min_thresh=min_thresh[var],
                    return_hst=hst_return_bool,
                    interp='linear',
                    dask_return=True
                    )

                if hst_return_bool:

                    hst_ba = qdm[0]
                    hst_ba = hst_ba.compute()

                    for yr in range(hst_yr[0],hst_yr[1]+1):

                        fn = dest / ("%s_%s_%d.nc" % (var,gcm,yr))
                        yr_slice = slice(str(yr),str(yr))
                        export_ds = hst_ba.sel(time=yr_slice)
                        export_ds = export_ds.astype('float32')
                        export_ds.to_netcdf(fn,engine='h5netcdf')
                    
                    del hst_ba
                
                sim_ba = qdm[-1]
                sim_ba = sim_ba.compute()

                for yr in range(sim_yr[0],sim_yr[1]+1):

                    fn = dest / ("%s_%s_%d.nc" % (var,gcm,yr))
                    yr_slice = slice(str(yr),str(yr))
                    export_ds = sim_ba.sel(time=yr_slice)
                    export_ds = export_ds.astype('float32')
                    export_ds.to_netcdf(fn,engine='h5netcdf')

                pbar.update()