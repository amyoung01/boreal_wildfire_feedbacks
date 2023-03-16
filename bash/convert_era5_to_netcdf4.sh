#!/bin/bash

# Define working/parent directory
# Find directory of current file, source: https://stackoverflow.com/a/246128
WDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Set array of year values to process
YR=($(seq 1979 1 2020))
VAR=('2m_temperature' \
     '2m_dewpoint_temperature' \
     '10m_u_component_of_wind' \
     '10m_v_component_of_wind' \
     'total_precipitation')

for i in ${YR[@]}; do

  for j in ${VAR[@]}; do
    
    echo $WDIR/tmp/$i"_era5_reanalysis_"$j".nc"

    nccopy -k nc7 \
      $WDIR/tmp/$i"_era5_reanalysis_"$j".nc" \
      $WDIR/data/raw/climate/era5/$i"_era5_reanalysis_"$j".nc"

    rm $WDIR/tmp/$i"_era5_reanalysis_"$j".nc"

  done

done
