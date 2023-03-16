#!/bin/bash

###############################################################################
# Initialize environment and variables
###############################################################################

# Set up directory names

# Find directory of current file, source: https://stackoverflow.com/a/246128
WDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DEST=$WDIR/../data/processed/veg/mod44b

mkdir -p $DEST

# Get fire year range from config.yaml using 'yq' package 
# (https://github.com/mikefarah/yq)
# Map extent (meters)
EXTENT=( \
  $(yq '.EXTENT.proj_lims[0]' $WDIR/../wildfire_analysis/config.yaml) \
  $(yq '.EXTENT.proj_lims[1]' $WDIR/../wildfire_analysis/config.yaml) \
  $(yq '.EXTENT.proj_lims[2]' $WDIR/../wildfire_analysis/config.yaml) \
  $(yq '.EXTENT.proj_lims[3]' $WDIR/../wildfire_analysis/config.yaml) \
)

# Spatial reference system information
CRS=$WDIR/../data/ancillary/AK_Canada_aea.prj

# Only do these files for now to save on storage
FILES=(
      $( ls $WDIR/../data/raw/veg/mod44b/*Percent_Tree_Cover*.tif )
      $( ls $WDIR/../data/raw/veg/mod44b/*Quality*.tif )
      $( ls $WDIR/../data/raw/veg/mod44b/*Cloud*.tif )
    )

for f in ${FILES[@]}; do

  gdalwarp \
    -tr 250 250 \
    -te ${EXTENT[@]} \
    -t_srs $CRS \
    -overwrite \
    $f $DEST/$( basename "$f" )

done
