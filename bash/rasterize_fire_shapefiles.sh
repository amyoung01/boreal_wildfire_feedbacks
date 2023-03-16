#!/bin/bash

###############################################################################
# Initialize environment and variables
###############################################################################

# Set up directory names

# Find directory of current file, source: https://stackoverflow.com/a/246128
WDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Get fire year range from config.yaml using 'yq' package 
# (https://github.com/mikefarah/yq)
YR1=$(yq '.TIME.fire_yr[0]' $WDIR/../wildfire_analysis/config.yaml)
YR2=$(yq '.TIME.fire_yr[1]' $WDIR/../wildfire_analysis/config.yaml)
YRS=($(seq $YR1 1 $YR2))

# Location of shapefile to rasterize
WDIR=$WDIR/../data/processed/fire/shapefiles
DEST=$WDIR/../rasters

# Map extent (meters)
EXTENT=( \
  $(yq '.EXTENT.proj_lims[0]' $WDIR/../wildfire_analysis/config.yaml) \
  $(yq '.EXTENT.proj_lims[1]' $WDIR/../wildfire_analysis/config.yaml) \
  $(yq '.EXTENT.proj_lims[2]' $WDIR/../wildfire_analysis/config.yaml) \
  $(yq '.EXTENT.proj_lims[3]' $WDIR/../wildfire_analysis/config.yaml) \
)

BAND_META=Description

for yr in ${YRS[@]}; do

  # Output file containing fire occurrence for AK and Canada
  RAST_FN=$DEST/AK_Canada_Fire_Occurrence_$yr.tif
  STACK_FN=$DEST/AK_Canada_Fire_Occurrence_1950_2020.tif

  # Rasterize polygons for AK and Canada for each year and store in tmp files
  gdal_rasterize \
    -init 0 \
    -burn 1 \
    -te ${EXTENT[@]} \
    -tr 1000 1000 \
    -where "FIREYR"=${yr} \
    -ot Byte \
    $WDIR/AK_Canada_large_fire_history.shp $RAST_FN

  # Add metadata for specific year
  gdal_edit.py -mo ${BAND_META}=${yr} $RAST_FN

done
