#!/bin/bash

# Find directory of current file, source: https://stackoverflow.com/a/246128
WDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

GCMS=( \
  $(yq '.CLIMATE.gcm_list[0]' $WDIR/wildfire_analysis/config.yaml) \
  $(yq '.CLIMATE.gcm_list[1]' $WDIR/wildfire_analysis/config.yaml) \
  $(yq '.CLIMATE.gcm_list[2]' $WDIR/wildfire_analysis/config.yaml) \
  $(yq '.CLIMATE.gcm_list[3]' $WDIR/wildfire_analysis/config.yaml) \
)

for gcm in ${GCMS[@]}; do

  mkdir -p $WDIR/data/raw/climate/cmip6/$gcm
  cd $WDIR/data/raw/climate/cmip6/$gcm

  bash $WDIR/bash/z_wget/wget-$gcm.sh -H

done

# Change directory back to working directory
cd $WDIR
