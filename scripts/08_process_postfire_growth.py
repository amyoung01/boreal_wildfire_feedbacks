import subprocess

import wildfire_analysis.data_processing.tree_cover_histories \
    as tree_cover_histories

# Calculate average tree cover for each fire perimeter and time-since-fire. 
# This script takes several hours to complete
tree_cover_histories()

# Run R script to average treecover values for each time since fire value and
# then generate a monotonically increasing spline function modeling tree cover
# as a function of time since fire.
rscript_call = 'Rscript --vanilla R/model_postfire_veg.R'
rscript_call = rscript_call.split(" ")

subprocess(rscript_call)