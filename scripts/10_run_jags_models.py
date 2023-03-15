import subprocess
from pathlib import Path

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

jags_rscript = root_dir / '../R/run_jags_models.R'
jags_model = root_dir / '../R/aab_bayesian_gamma_regression.txt'

subpr_call = 'Rscript --vanilla %s %s' % (jags_rscript, jags_model)

subpr_call = subpr_call.split(" ")

subprocess.run(subpr_call)