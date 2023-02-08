#!/bin/bash
#
# 1_organize_fire_data.sh
# -----------------------------------------------------------------------------
# 
# Read in raw fire polygon shapefiles for AK and Canada and complete the 
# following steps:
# 1. Make sure each file is '.shp' and '.gdb' and also reproject to 
#    predetermined spatial reference system.
# 2. Create field in each shape file "FIREYR" that is simply an integer of
#    the year the fire occurred.
# 3. Select all fires in each dataset from 1950-2020 using SQL statement.
# 4. Rasterize each layer for each year, burning a value of 1 if a fire occurred
#    and a value of 0 if it did not. Then use raster calculator to create one 
#    map for fire presence/absence for each year in boreal N. America.
# 5. Export as GeoTIFF
#
# Dependencies: 
#   -GDAL 3.4.1, released 2021/12/27
#   -Pre-defined spatial reference system (srs) information: ak_canada_aea.prj
#
# Notes:
#   -AK Fire History was available for download in ESRI GeoDataBase format. 
#    This was converted to a shapefile in QGIS before processing in script 
#    below.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Initialize workspace 
# -----------------------------------------------------------------------------

# Acivate required conda env
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py39

echo "Reprojecting and rasterizing shapefiles:"
echo "Using "$(gdalinfo --version)" for shapefile management."

# Define working/parent directory
WDIR=~/projects/boreal_fire_feedbacks

# Define up source and destination (target) directories and file names
AK_SRC=$WDIR/data/fire/large_fires/AK_LFDB_poly_large_fires.shp
CAN_SRC=$WDIR/data/fire/large_fires/CAN_NFDB_poly_large_fires.shp

AK_DEST=$WDIR/processed_data/fire/AKFIRE/AK_FireHistory_Polygons.shp
CAN_DEST=$WDIR/processed_data/fire/CANFIRE/Canada_FireHistory_Polygons.shp

# Spatial Reference System for output
SRS=$WDIR/data/ancillary_data/ak_canada_aea.prj

# Map extent (meters)
EXTENT=(-2774040 -238112 4064154 3237655)

# Set array of year values to process
YR=($(seq 1950 1 2020))

# Create names for temp files that will store intermediary steps. Removed in 
# each iteration of for loop in steps 4 and 5.
tmpfile_1=$WDIR/tmp/tmpraster_1.tif
tmpfile_2=$WDIR/tmp/tmpraster_2.tif

# -----------------------------------------------------------------------------
# Step 1: Reproject shapefiles to predefined reference system.
# -----------------------------------------------------------------------------
ogr2ogr -f 'ESRI Shapefile' -t_srs $SRS $AK_DEST $AK_SRC
ogr2ogr -f 'ESRI Shapefile' -t_srs $SRS $CAN_DEST $CAN_SRC

# -----------------------------------------------------------------------------
# Step 2: Convert FIREYEAR field from string to integer and rename as 
# 'FIREYR' in Alaska. For Canada, create new field 'FIREYR' from 'YEAR'.
# -----------------------------------------------------------------------------
ogr2ogr -overwrite -nln 'AK_FireHistory_Polygons' \
  -sql "SELECT *, CAST(FIREYEAR as integer) AS FIREYR FROM AK_FireHistory_Polygons" \
  $AK_DEST $AK_DEST
ogr2ogr -overwrite -nln 'Canada_FireHistory_Polygons' \
  -sql "SELECT *, YEAR AS FIREYR FROM Canada_FireHistory_Polygons" \
  $CAN_DEST $CAN_DEST

# -----------------------------------------------------------------------------
# Step 3: Keep only those polygons between 1950 and 2020 for AK and Canada.
# -----------------------------------------------------------------------------
ogr2ogr -overwrite -nln 'AK_FireHistory_Polygons' \
  -sql "SELECT * FROM AK_FireHistory_Polygons WHERE (FIREYR >= 1950) AND (FIREYR <= 2020)" \
  $AK_DEST $AK_DEST
ogr2ogr -overwrite -nln 'Canada_FireHistory_Polygons' \
  -sql "SELECT * FROM Canada_FireHistory_Polygons WHERE (FIREYR >= 1950) AND (FIREYR <= 2020)" \
  $CAN_DEST $CAN_DEST

# -----------------------------------------------------------------------------
# Steps 4 and 5: In for loop below, rasterize fire polygons for each year and
# store in temporary files. In these rasters there are two values: 1 = fire and 
# 0 = no fire. "Add" these two maps together using gdal_calc.py to get fire
# occurrence for AK and Canada on single map. Export this map as GeoTIFF file.
# -----------------------------------------------------------------------------

for i in ${YR[@]}; do

  # Output file containing fire occurrence for AK and Canada
  RAST_FN=$WDIR/processed_data/fire/raster/AK_Canada_Fire_Occurrence_$i.tif

  # Rasterize polygons for AK and Canada for each year and store in tmp files
  gdal_rasterize -init 0 -burn 1 -te ${EXTENT[@]} -tr 1000 1000 \
    -sql "SELECT * FROM AK_FireHistory_Polygons WHERE (FIREYR="${i}")" \
    $AK_DEST $tmpfile_1
  gdal_rasterize -init 0 -burn 1 -te ${EXTENT[@]} -tr 1000 1000 \
    -sql "SELECT * FROM Canada_FireHistory_Polygons WHERE (FIREYR="${i}")" \
    $CAN_DEST $tmpfile_2

  # Add rasterized layers for AK and Canada to get single map and export
  gdal_calc.py -A $tmpfile_1 -B $tmpfile_2 --calc="A+B" --outfile=$RAST_FN \
    --overwrite --type=Byte --quiet

  # Clear out project tmp directory
  rm $tmpfile_1 $tmpfile_2

done

# Deactivate conda environment
conda deactivate

# End of script ---------------------------------------------------------------