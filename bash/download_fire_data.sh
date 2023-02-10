#!/bin/bash

###############################################################################
#
# Initialize environment and variables
#
###############################################################################

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py39

# Set up directory names

# Find directory of current file, source: https://stackoverflow.com/a/246128
WDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Spatial reference system information
PRJ=$WDIR/../data/ancillary/AK_Canada_aea.prj

# Designate and create directories
DATA_DIR=$WDIR/../data/raw/fire/
DEST=$WDIR/../data/processed/fire/shapefiles
AK_DIR=$DATA_DIR/Alaska/
CAN_DIR=$DATA_DIR/Canada/

mkdir -p $AK_DIR
mkdir -p $CAN_DIR
mkdir -p $DEST

###############################################################################
#
# Download fire datasets for Alaska and Canada
#
###############################################################################

# Download Alaska fire history
cd $AK_DIR
echo
echo "Downloading Alaska fire polygons ..."
echo
curl -o ak_fire.zip https://fire.ak.blm.gov/content/maps/aicc/Data/Data%20%28zipped%20filegeodatabases%29/AlaskaFireHistory_Polygons_1940_2020.zip -L
unzip ak_fire.zip
echo " ... finished downloading Alaska fire datasets!"

# Download Canada fire history
cd $CAN_DIR
echo
echo "Downloading Canada fire polygons ..."
echo
curl -o can_fire.zip https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly_large_fires.zip -L
unzip can_fire.zip
echo "finished downloading Canada fire datasets."

# For Alaska, also need to convert from geodatabase (.gdb) to shapefile (.shp).
# Also, for Alaska, limit to "large" fire events and remove all fire perimeters 
# < 200 ha.

###############################################################################
#
# Process AK fire history
# -----------------------
#
# In the next steps for the Alaska fire dataset:
#  1. Convert Alaska fire geodatabase to a shapefile and reproject to 
#     predetermined spatial reference system
#  2. Select all fire years between 1950-2020 and > 200 hectares (494.5 acres)
#  3. Trim fields in shapefile to only FIREYR and ACRES
#
###############################################################################

echo
echo "Using "$(gdalinfo --version)" for shapefile management ..."
echo

# Get name of downloaded geodatabse
GDB_NAME=$(basename -- *.gdb)

# Set tmp files for writing intermediate data processing steps
TMP1=tmp1.shp
TMP2=tmp2.shp
TMP3=tmp3.shp
TMP4=tmp4.shp

#  1. Convert Alaska fire geodatabase to a shapefile and reproject to 
#  predetermined spatial reference system

ogr2ogr -t_srs $PRJ -f "ESRI Shapefile" $DEST/$TMP1 $GDB_NAME > /dev/null 2>&1

# 2. Select all fire years between 1950-2020 and > 200 hectares (494.5 acres).
# First need to convert FIREYEAR field from string to integer and 
# rename 'FIREYR'. 
# 
# '> /dev/null 2>&1' blocks output to terminal

ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT *, CAST(FIREYEAR as integer) AS FIREYR FROM tmp1" \
   $DEST/$TMP2 $DEST/$TMP1 > /dev/null 2>&1

ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT * FROM tmp2 WHERE (FIREYR >= 1950) AND \
                                 (FIREYR <= 2020) AND \
                                 (ACRES > 494.5)" \
  $DEST/$TMP3 $DEST/$TMP2 > /dev/null 2>&1

# 3. Trim fields in shapefile to only FIREYR and ACRES

ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT FIREYR, ACRES FROM tmp3" \
  $DEST/AK_LFDB_poly_large_fires.shp $DEST/$TMP3 > /dev/null 2>&1

# Remove/delete temporary files

rm $DEST/tmp*

SHP_NAME=$(basename -- *.shp)

ogr2ogr -t_srs $PRJ -f "ESRI Shapefile" \
  $DEST/$TMP1 $SHP_NAME > /dev/null 2>&1

ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT *, YEAR AS FIREYR FROM tmp1" \
  $DEST/$TMP2 $DEST/$TMP1 > /dev/null 2>&1

# Convert HA to ACRES by multiplying by a factor of 2.471
ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT *, SIZE_HA*2.471 AS ACRES FROM tmp2" \
  $DEST/$TMP3 $DEST/$TMP2 > /dev/null 2>&1

ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT * FROM tmp3 WHERE (FIREYR >= 1950) AND (FIREYR <= 2020)" \
  $DEST/$TMP4 $DEST/$TMP3 > /dev/null 2>&1

ogr2ogr -f "ESRI Shapefile" \
  -sql "SELECT FIREYR, ACRES FROM tmp4" \
  $DEST/CAN_NFDB_poly_large_fires.shp $DEST/$TMP4 > /dev/null 2>&1

ogr2ogr -f "ESRI Shapefile" \
  $DEST/AK_Can_large_fire_history_1950-2020.shp \
  $DEST/AK_LFDB_poly_large_fires.shp > /dev/null 2>&1
  
ogr2ogr -f "ESRI Shapefile" -update -append \
  $DEST/AK_Can_large_fire_history_1950-2020.shp \
  $DEST/CAN_NFDB_poly_large_fires.shp \
  -nln "AK_Can_large_fire_history_1950-2020" > /dev/null 2>&1

rm $DEST/tmp* $DEST/AK_LFDB_poly_large_fires* $DEST/CAN_NFDB_poly_large_fires*