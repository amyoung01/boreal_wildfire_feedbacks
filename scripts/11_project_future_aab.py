import subprocess
from pathlib import Path

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

predfire_rscript = root_dir / '../R/project_future_fire.R'

subpr_call = 'Rscript --vanilla %s' % predfire_rscript

subpr_call = subpr_call.split(" ")

subprocess.run(subpr_call)