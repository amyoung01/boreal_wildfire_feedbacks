#!/usr/bin/env python3

#%% Import libraries
import yaml
from pathlib import Path

import pandas as pd
import numpy as np

#%% Import config file and read in parameters needed for data processing
# Get global values from configuration file
# Read in configuration list from 
config_fn = Path('../wildfire_analysis/config.yaml')

with open(config_fn, 'r') as config_fn:
    config_params = yaml.safe_load(config_fn)

    gcm_list = config_params['CLIMATE']['gcm_list']

#%% Set directory names
dataframe_dir = Path('../data/dataframes')
projaab_dir = Path('../data/model_results/projected_area_burned')

#%% Read in historical observed AAB
hist_aab = pd.read_csv(dataframe_dir / 'annual_area_burned.csv')
hist_aab = hist_aab.loc[hist_aab['year'] >= 1980]
hist_aab = hist_aab.reset_index(drop=True)

#%% Read in data on ecoregion size
ecos_size = pd.read_dcsv(Path('../data/ancillary/ecoregion_size.csv'))

#%% Finish initializing workspace
ecos = hist_aab['ecos'].unique() # Unique ecoregions
yr = np.arange(1980, 2099+1) # Years to process
feedback_type = ['feedback', 'no-feedback'] # Feedback type
# Percentiles to summarize
quantvals = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95] 

# Column labels for dataframe to export
col_labels = ['year', 'ecos', 'ecos_size', 'gcm', 'obs_aab', 'feedback_type', 
              'mean', 'sd', 'prctile05', 'prctile10', 'prctile25', 'prctile50',
              'prctile75', 'prctile90', 'prctile95']

# Create empty dataframe
export_df = pd.DataFrame(data=None, columns=col_labels)

# Total number of summaries to produce
n = yr.size * len(gcm_list) * len(feedback_type)

for ecos_id in ecos:

    export_df_i = pd.DataFrame(data=-9999.0 * np.ones((n, len(col_labels))), 
                               columns=col_labels)
    
    export_df_i['year'] = np.tile(yr, len(feedback_type) * len(gcm_list))
    export_df_i['ecos'] = ecos_id
    export_df_i['ecos_size'] = \
        ecos_size.loc[ecos_size['ecos'] == ecos_id, 'area_km2']
    export_df_i['gcm'] = np.repeat(gcm_list, len(feedback_type) * yr.size)
    export_df_i['feedback_type'] = \
        np.tile(np.repeat(feedback_type, yr.size), len(gcm_list))

    hist_aab_i = hist_aab.loc[hist_aab['ecos'] == ecos_id,
                              'annual_area_burned_km2']

    for gcm in gcm_list:     

        for fd in feedback_type:

            hst_yr_id = (export_df_i['gcm'] == gcm) \
                         & (export_df_i['feedback_type'] == fd) \
                         & ((export_df_i['year'] >= 1980) \
                             & (export_df_i['year'] <= 2020))
            
            proj_id = (export_df_i['gcm'] == gcm) \
                       & (export_df_i['feedback_type'] == 'feedback') \
                       & (export_df_i['year'] >= 2021)            
            
            export_df_i.loc[hst_yr_id, 'obs_aab'] = hist_aab_i.values   

            fn = list(projaab_dir.glob('*%s*_%s*%d*' % 
                                    (gcm, fd, ecos_id)))[0]
            feedback = pd.read_csv(fn)       

            mean_feedback = feedback.mean(axis=0)
            sd_feedback = feedback.std(axis=0)
            quantiles_feedback = feedback.quantile(q, axis=0)

            export_df_i.loc[proj_id, 'mean'] = mean_feedback.values
            export_df_i.loc[proj_id, 'sd'] = sd_feedback.values

            for q in quantvals:

                qid = quantiles_feedback.index == q
                aab_q = quantiles_feedback.loc[qid].values.flatten()

                export_df_i.loc[proj_id, 'prctile%02d' % (100 * q)] = aab_q
        
            export_df = pd.concat((export_df, export_df_i),
                                   axis=0, 
                                   ignore_index=True)

# Rounfd all area burned results to one decimal place
export_df = export_df.round(1)

# Add header with metadata to csv file that is exported
fn = Path('../data/dataframes/aab_timeseries_summaries.csv')
commented_lines = ['# aab_timeseries_summaries.csv\n', 
                   '# Units of annual area burned are in km^2\n',
                   '# -9999 = NoData\n'
                   '# Summaries provided are:\n',
                   '# \t ecos_size: area of entire ecoregion in km^2\n'
                   '# \t obs_aab: historical observed annual area burned\n'
                   '# \t mean: average of all simulations\n',
                   '# \t sd: standard deviation of simulations\n',
                   '# \t prctile05: 5th percentile of simulations\n',
                   '# \t prctile10: 10th percentile of simulations\n',
                   '# \t prctile25: 25th percentile of simulations\n',
                   '# \t prctile50: 50th percentile of simulations\n',
                   '# \t prctile75: 75th percentile of simulations\n',
                   '# \t prctile90: 90th percentile of simulations\n',
                   '# \t prctile95: 95th percentile of simulations\n',
                   '#\n']

with open(fn, 'w') as f:
    f.write("".join(commented_lines))

export_df.to_csv(fn, mode='a', index=False)
 