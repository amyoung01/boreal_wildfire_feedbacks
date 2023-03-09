import subprocess
import yaml
from pathlib import Path

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:
    config_params = yaml.safe_load(config_file)

    dataframes_dir = root_dir / config_params['PATHS']['dataframes_data_dir']
    results_dir = root_dir / config_params['PATHS']['model_results_data_dir']

jags_rscript = root_dir / '../R/run_jags_models.R'
jags_model = root_dir / '../R/aab_bayesian_gamma_regression.txt'

subpr_call = 'Rscript --vanilla %s %s %s %s' % (jags_rscript,
                                                dataframes_dir,
                                                results_dir,
                                                jags_model)

subpr_call = subpr_call.split(" ")

subprocess.run(subpr_call)