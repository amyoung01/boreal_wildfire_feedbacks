#!/usr/bin/env python3

#%% Import libraries
import yaml
from pathlib import Path

import pandas as pd
import numpy as np

#%% Import config file and read in parameters needed for data processing
# Get global values from configuration file
# Read in configuration list from 
config_fn = Path('wildfire_analysis/config.yaml')

with open(config_fn, 'r') as config_fn:
    config_params = yaml.safe_load(config_fn)

    gcm_list = config_params['CLIMATE']['gcm_list']

sources = ['era5'] + gcm_list

#%% Set directory names
dataframe_dir = Path('data/dataframes')
projaab_dir = Path('data/model_results/projected_area_burned')

#%% Read in data on ecoregion size
ecos_size = pd.read_csv(Path('data/ancillary/ecoregion_size.csv'))

#%% Finish initializing workspace
ecos = ecos_size['ecos'].unique() # Unique ecoregions
yr = np.arange(1980, 2099+1) # Years to process
feedback_type = ['feedback', 'no-feedback'] # Feedback type

# Percentiles to summarize
quantvals = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95] 

# Create empty dataframe
export_df = pd.DataFrame()

for ecos_id in ecos:

    for src in sources:     

        for fd in feedback_type:       

            fn = list(projaab_dir.glob('future-fire-projections*%s*_%s*%d*' % 
                                    (src, fd, ecos_id)))[0]
            aab = pd.read_csv(fn)

            cumul_aab = pd.DataFrame.cumsum(aab, axis=1)

            ecos_size_i = \
                ecos_size.loc[ecos_size['ecos'] == ecos_id,'area_km2'].values

            mean_aab = aab.mean(axis=0)
            sd_aab = aab.std(axis=0)

            mean_cumul = cumul_aab.mean(axis=0)
            sd_cumul = cumul_aab.std(axis=0)

            data = {
                'year': np.array(aab.columns).astype('int').tolist(),
                'ecos': ecos_id,
                'ecos_size': ecos_size_i[0],
                'source': src,
                'feedback_type': fd,
                'annual_mean': mean_aab.values.tolist(),
                'annual_sd': sd_aab.values.tolist(),
                'cumul_mean': mean_cumul.values.tolist(),
                'cumul_sd': sd_cumul.values.tolist()
            }

            aab_quantiles_feedback = aab.quantile(quantvals, axis=0)
            cumul_aab_quantiles_feedback = cumul_aab.quantile(quantvals, axis=0)

            for q in quantvals:

                qid = aab_quantiles_feedback.index == q                
                aab_q = aab_quantiles_feedback.loc[qid].values.flatten()
                data.update({'annual_prctile%02d' % (100 * q): aab_q.tolist()})

            for q in quantvals:

                qid = cumul_aab_quantiles_feedback.index == q
                cumul_q = cumul_aab_quantiles_feedback.loc[qid].values.flatten()                             
                data.update({'cumulative_prctile%02d' % (100 * q): cumul_q.tolist()})
        
            export_df = pd.concat((export_df, pd.DataFrame.from_dict(data)),
                                   axis=0, 
                                   ignore_index=True)

# Rounfd all area burned results to one decimal place
export_df = export_df.round(1)

# Add header with metadata to csv file that is exported
fn = Path('data/dataframes/projected_aab_summaries.csv')
commented_lines = [
    '# projected_aab_summaries.csv\n',
    '# Units of annual area burned are in km^2\n',
    '# -9999 = NoData\n'
    '# Columns provided are:\n',
    '# \t sources: data source for predictions"," either ERA5 or a GCM\n',
    '# \t feedback_type: simulation run"," either feedback or no-feedback\n',
    '# \t ecos_size: area of entire ecoregion in km^2\n'
    '# \t annual_mean: average of annual area burned in a given year\n',
    '# \t annual_sd: standard deviation of annual area burned in a given year\n',
    '# \t cumul_mean: average of cumulative area burned in a given year\n',
    '# \t cumul_sd: standard deviation of cumulative area burned in a given year\n',
    '# \t annual_prctile05: 5th percentile of annual area burned in a given year\n',
    '# \t annual_prctile10: 10th percentile of annual area burned in a given year\n',
    '# \t annual_prctile25: 25th percentile of annual area burned in a given year\n',
    '# \t annual_prctile50: 50th percentile of annual area burned in a given year\n',
    '# \t annual_prctile75: 75th percentile of annual area burned in a given year\n',
    '# \t annual_prctile90: 90th percentile of annual area burned in a given year\n',
    '# \t annual_prctile95: 95th percentile of annual area burned in a given year\n',
    '# \t cumulative_prctile05: 5th percentile of cumulative area burned in a given year\n',
    '# \t cumulative_prctile10: 10th percentile of cumulative area burned in a given year\n',
    '# \t cumulative_prctile25: 25th percentile of cumulative area burned in a given year\n',
    '# \t cumulative_prctile50: 50th percentile of cumulative area burned in a given year\n',
    '# \t cumulative_prctile75: 75th percentile of cumulative area burned in a given year\n',
    '# \t cumulative_prctile90: 90th percentile of cumulative area burned in a given year\n',
    '# \t cumulative_prctile95: 95th percentile of cumulative area burned in a given year\n',    
    '#\n'
    ]

with open(fn, 'w') as f:
    f.write("".join(commented_lines))

export_df.to_csv(fn, mode='a', index=False)
 