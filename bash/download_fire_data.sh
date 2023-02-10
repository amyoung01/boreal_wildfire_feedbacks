#!/bin/bash

###############################################################################
# Initialize environment and variables
###############################################################################

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py39

# Set up directory names

# Find directory of current file, source: https://stackoverflow.com/a/246128
WDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Spatial reference system information
PRJ=$WDIR/../data/ancillary/AK_Canada_aea.prj

# Get fire year range from config.yaml using 'yq' package 
# (https://github.com/mikefarah/yq)
YR1=$(yq '.TIME.fire_yr[0]' $WDIR/../wildfire_analysis/config.yaml)
YR2=$(yq '.TIME.fire_yr[1]' $WDIR/../wildfire_analysis/config.yaml)

# Designate and create directories
DATA_DIR=$WDIR/../data/raw/fire/
DEST=$WDIR/../data/processed/fire/shapefiles
AK_DIR=$DATA_DIR/Alaska/
CAN_DIR=$DATA_DIR/Canada/

mkdir -p $AK_DIR
mkdir -p $CAN_DIR
mkdir -p $DEST

###############################################################################
# Download fire datasets for Alaska and Canada
###############################################################################

# Download Alaska fire history
# cd $AK_DIR
# echo
# echo "Downloading Alaska fire polygons ..."
# echo
# curl -o ak_fire.zip https://fire.ak.blm.gov/content/maps/aicc/Data/Data%20%28zipped%20filegeodatabases%29/AlaskaFireHistory_Polygons_1940_2022.zip -L
# unzip ak_fire.zip
# echo " ... finished downloading Alaska fire datasets!"

# # Download Canada fire history
# cd $CAN_DIR
# echo
# echo "Downloading Canada fire polygons ..."
# echo
# curl -o can_fire.zip https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly_large_fires.zip -L
# unzip can_fire.zip
# echo "finished downloading Canada fire datasets."

###############################################################################
# Process AK fire history
# -----------------------
# In the next steps for the Alaska fire dataset:
#  1. Convert Alaska fire geodatabase to a shapefile and reproject to 
#     predetermined spatial reference system
#  2. Select all fire years between 1950-2020 and > 200 hectares (494.5 acres)
#  3. Trim fields in shapefile to only FIREYR and ACRES
###############################################################################

echo
echo "Using "$(gdalinfo --version)" for shapefile management ..."
echo

cd $AK_DIR

# Get name of downloaded geodatabse
GDB_NAME=$(basename -- *.gdb)

#  1. Convert Alaska fire geodatabase to a shapefile and reproject to 
#  predetermined spatial reference system
#
#       '> /dev/null' prevents output from displaying to terminal
#
ogr2ogr -f "ESRI Shapefile" \
  -t_srs $PRJ \
  $DEST/tmp.shp $GDB_NAME > /dev/null

# 2. Add column to attribute table signaling original data source (e.g., either
# Alaska large fire database [AK_LFDB] or Canadian National Fire Database 
# [CAN_NFDB]).
ogrinfo $DEST/tmp.shp \
  -sql "ALTER TABLE tmp ADD COLUMN DATASRC character(8)" > /dev/null
ogrinfo $DEST/tmp.shp -dialect SQLite \
  -sql "UPDATE tmp SET DATASRC = 'AK_LFDB'" > /dev/null
 
# 3. Select all fire years between 1950-2020 and > 200 hectares .
# First need to convert FIREYEAR field from string to integer and 
# rename 'FIREYR'. 
ogr2ogr -f "ESRI Shapefile" -overwrite \
  -sql "SELECT *, CAST(FIREYEAR as integer) AS FIREYR FROM tmp" \
   $DEST/tmp.shp $DEST/tmp.shp -nln 'tmp' > /dev/null

# Convert from ACRES -> HECTARES: HECTARES = 0.4047*ACRES
ogr2ogr -f "ESRI Shapefile" -overwrite \
  -sql "SELECT *, 0.4047*ACRES AS HECTARES, NAME AS FIRENAME FROM tmp" \
   $DEST/tmp.shp $DEST/tmp.shp -nln 'tmp' > /dev/null

ogr2ogr -f "ESRI Shapefile" -overwrite \
  -sql "SELECT * FROM tmp WHERE (FIREYR >= $YR1) AND \
                                (FIREYR <= $YR2) AND \
                                (HECTARES >= 200.0)" \
  $DEST/tmp.shp $DEST/tmp.shp -nln 'tmp' > /dev/null

# 3. Trim fields (or attributes) in shapefile to only FIREYR and ACRES
ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT DATASRC, FIRENAME, FIREYR, HECTARES FROM tmp" \
  $DEST/AK_LFDB_poly_large_fires.shp $DEST/tmp.shp > /dev/null

# Remove/delete temporary files
rm $DEST/tmp*

# ###############################################################################
# # Process Canada fire history
# # ---------------------------
# # In the next steps for the Alaska fire dataset:
# #  1. Reproject Canada fire shapefile to predetermined spatial reference system
# #  2. Rename FIREYEAR to FIREYR to match AK shapefile
# #  3. Convert SIZE_HA attribute to ACRES by multiplying by a factor of 2.471
# #  4. Select all fire years between 1950-2020. Downloaded shapefile already
# #     filters for large fires > 200 ha
# #  3. Trim fields in shapefile to only FIREYR and ACRES
# ###############################################################################

cd $CAN_DIR

# # Get name of downloaded shapefile
SHP_NAME=$(basename -- *.shp)

# 1. Reproject Canada fire shapefile
ogr2ogr -f "ESRI Shapefile" \
  -t_srs $PRJ \
  $DEST/tmp.shp $SHP_NAME > /dev/null

# 2. Add column to attribute table signaling original data source (e.g., either
# Alaska large fire database [AK_LFDB] or Canadian National Fire Database 
# [CAN_NFDB]).
ogrinfo $DEST/tmp.shp \
  -sql "ALTER TABLE tmp ADD COLUMN DATASRC character(8)" > /dev/null
ogrinfo $DEST/tmp.shp -dialect SQLite \
  -sql "UPDATE tmp SET DATASRC = 'CAN_NFDB'" > /dev/null
 
# 3. Select all fire years between 1950-2020 and > 200 hectares (494.5 acres).
# First need to convert FIREYEAR field from string to integer and 
# rename 'FIREYR'. 
ogr2ogr -f "ESRI Shapefile" -overwrite \
  -sql "SELECT *, YEAR AS FIREYR, SIZE_HA AS HECTARES FROM tmp" \
   $DEST/tmp.shp $DEST/tmp.shp -nln 'tmp' > /dev/null

ogr2ogr -f "ESRI Shapefile" -overwrite \
  -sql "SELECT * FROM tmp WHERE (FIREYR >= $YR1) AND (FIREYR <= $YR2)" \
  $DEST/tmp.shp $DEST/tmp.shp -nln 'tmp' > /dev/null

# 4. Trim fields (or attributes) in shapefile to DATASRC, FIRENAME, FIREYR and 
# ACRES
ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT DATASRC, FIRENAME, FIREYR, HECTARES FROM tmp" \
  $DEST/CAN_NFDB_poly_large_fires.shp $DEST/tmp.shp > /dev/null

# Remove/delete temporary files
rm $DEST/tmp*

# ##############################################################################
# Merge AK and Canada fire history shapefiles into single shapefile and 
# delete individual files for AK and Canada
# ##############################################################################

# First, create new shapefile with merged name using AK fire history
ogr2ogr -f "ESRI Shapefile" \
  $DEST/AK_Can_large_fire_history_$YR1-$YR2.shp \
  $DEST/AK_LFDB_poly_large_fires.shp > /dev/null

# Second, update merged shapefile by appending Canada fire history shapefile
ogr2ogr -f "ESRI Shapefile" -update -append \
  $DEST/AK_Can_large_fire_history_$YR1-$YR2.shp \
  $DEST/CAN_NFDB_poly_large_fires.shp \
  -nln "AK_Can_large_fire_history_$YR1-$YR2" > /dev/null

# Finally, remove AK and Canada files
rm $DEST/AK_LFDB_poly_large_fires* 
rm $DEST/CAN_NFDB_poly_large_fires*