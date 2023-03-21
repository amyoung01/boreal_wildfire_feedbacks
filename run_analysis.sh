#!/bin/bash

# Author: Adam Young (https://github.com/amyoun01)
# Creation Date: 2023-03-12

# -----------------------------------------------------------------------------
# Machine information
# ProductName:            macOS
# ProductVersion:         13.0.1
# BuildVersion:           22A400
# Architecture:           arm64
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Make sure the following prerequisties are installed:
# 1. miniconda (conda version 4.12.0) 
# 2. homebrew (3.6.21)
# 3. curl (7.84.0)
# 4. Login ability to download data from the following public data sources:
#     - ERA5 Climate Data: https://cds.climate.copernicus.eu/api-how-to
#     - CMIP6 GCM Output LLNL node: https://esgf-node.llnl.gov/projects/cmip6/
#     - NASA AppEEARS for MODIS datasets: https://appeears.earthdatacloud.nasa.gov

# Further pre-reqs installed via this script are:
# 5. Using homebrew:
#     - wget 1.21.3
#     - yq v4.30.8
#     - jags 4.3.1
# 6. Python 3.9.15. Required libraries below and listed in requirements.txt:
#     - cdsapi=0.5.1
#     - dask=2022.12.1
#     - gdal=3.6.2
#     - geopandas=0.12.2
#     - h5netcdf=1.1.0
#     - h5py=3.7.0
#     - netcdf4=1.6.2
#     - numpy=1.23.5
#     - pandas=1.5.2
#     - pyproj=3.4.1
#     - pyyaml=6.0
#     - rasterio=1.3.4
#     - shapely=2.0.0
#     - tqdm=4.64.1
#     - xarray=2022.12.0
#     - xclim=0.40.0
# 7. R (base) 4.2.2. Required libraries:
#     - actuar; Actuarial Functions and Heavy Tailed Distributions (v3.3-1)
#     - car; Companion to Applied Regression (v3.1-1)
#     - data.table; Extension of 'data.frame' (v1.14.6)
#     - fitdistrplus; Fit Parametric Distributions (v1.1-8)
#     - R2jags; Using R to Run 'JAGS' (v0.7-1)
#     - scam; Shape Constrained Additive Models (v1.2-13)

# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Create conda env and install required libraries
# -----------------------------------------------------------------------------

# Use homebrew to install required packages/libraries. Commented out for now.
# brew install wget
# brew install yq
# brew install jags

conda create --name boreal-wildfire-analysis python=3.9.15 r-base=4.2.2

source ~/miniconda3/etc/profile.d/conda.sh
conda activate boreal-wildfire-analysis

conda install -c conda-forge \
  cdsapi=0.5.1 \
  dask=2022.12.1 \
  gdal=3.6.2 \
  geopandas=0.12.2 \
  h5netcdf=1.1.0 \
  h5py=3.7.0 \
  netcdf4=1.6.2 \
  numpy=1.23.5 \
  pandas=1.5.2 \
  pyproj=3.4.1 \
  pyyaml=6.0 \
  rasterio=1.3.4 \
  shapely=2.0.0 \
  tqdm=4.64.1 \
  xarray=2022.12.0 \
  xclim=0.40.0

# -----------------------------------------------------------------------------
# Install wildfire_analysis package locally
# -----------------------------------------------------------------------------
pip install .

# -----------------------------------------------------------------------------
# Install R packages. Doesn't install specific versions stated above  when 
# being run from R/install_req_pkgs.R. Should be improved. 
#
# ******
# TODO: Need to figure out how to install 'rjags' and 'R2jags' in a specific
# or new conda environment. Still not done
# ******
# -----------------------------------------------------------------------------

conda install -c r \
  r-essentials \
  r-car=3.1_1 \
  r-data.table=1.14.6

LIBPATH=$( Rscript -e "cat(.libPaths())" )
Rscript --vanilla R/install_req_pkgs.R $LIBPATH

# To generate token needed for MOD44B download see:
# https://appeears.earthdatacloud.nasa.gov/api/#authentication
EARTHDATA_TOKEN="[NEED TO INSERT EARTHDATA LOGIN TOKEN HERE]"

# Add script directories to current PATH
CWD=$( pwd )
PATH=$PATH:$CWD/bash:$CWD/R:$CWD/scripts

mkdir tmp # Create temporary directory to save intermediate datasets

# -----------------------------------------------------------------------------
# Download datasets 
# -----------------------------------------------------------------------------

# Download and unzip wwf ecoregion map
download_ecoregion_shapefiles.sh

# Download and organize fire data
downlad_fire_data.sh
rasterize_fire_shapefiles.sh

# Download and reproject MOD44B datasets
request_mod44b.sh $EARTHDATA_TOKEN
reproject_mod44b.sh

# Download CMIP6 datasets using wget scripts. These scripts were generated
# by the https://esgf-node.llnl.gov/projects/cmip6/ data cart and manually
# edited to only include years of interest. We don't provide the download
# scripts in the repository, but we do provide an empty text file named for 
# each netcdf downloaded in bash/z_wget_scripts/. The actual scripts are 
# available upon request from the author.

download_cmip6.sh

# Download ERA5 datasets using a set of python scripts wrapped in shell script.
# Also run script to convert these ERA5 netcdf files from NetCDF3 to NetCDF4.
python wildfire_analysis/utils/download_era5.py
convert_era5_to_netcdf4.sh

# -----------------------------------------------------------------------------
# Organize datasets for processing:
#   01_process_era5.py
#      Organize ERA5 datasets to get dailiy summaries of desired variables and
#      modify geographic extent and convert calendar to 'noleap'
#   02_process_cmip6.py
#      Organize all downloaded CMIP6 data by modifying geographic extent, 
#      converting calendar, and converting units (e.g., K -> degC)
#   03_modify_ecoregion_shapefile.py
#      Subset and reclass Ecoregions shapefile. Also use gdal to reproject 
#      ecoregion to predetermined spatial reference system.
# -----------------------------------------------------------------------------
01_process_era5.py --verbose
02_process_cmip6.py --verbose
03_modify_ecoregion_shapefile.py

# Also, project ecroregion shapefile from geographic to projected reference 
# system using gdal
ogr2ogr -f "ESRI Shapefile" \
  -t_srs data/ancillary/AK_Canada_aea.prj \
  data/processed/ecoregions/ecos_reproj.shp \
  data/processed/ecoregions/ecos.shp

# -----------------------------------------------------------------------------
# Bias correct GCM data 
#   This script uses a quantile delta mapping approach to 
# -----------------------------------------------------------------------------
04_bias_correct_gcms.py --verbose

# -----------------------------------------------------------------------------
# CFFDRS Calculations:
#   05_calculate_cffdrs.py
#      Calculate daily CFFDRS Indices
#   06_calculate_cffdrs_summaries.py
#      Get annual statistical summaries for each grid cell
#   07_generate_cffdrs_dataframes.py
#      Get spatial averages for each ecoregion
# -----------------------------------------------------------------------------
05_calculate_cffdrs.py --verbose
06_calculate_cffdrs_summaries.py --verbose
07_generate_cffdrs_dataframes.py

# -----------------------------------------------------------------------------
# TBD -------------------------------------------------------------------------
# -----------------------------------------------------------------------------
08_generate_areaburned_dataframes.py

# -----------------------------------------------------------------------------
# TBD -------------------------------------------------------------------------
# -----------------------------------------------------------------------------
09_process_postfire_growth.py

# -----------------------------------------------------------------------------
# TBD -------------------------------------------------------------------------
# -----------------------------------------------------------------------------

10_run_jags_models.py
11_project_future_aab.py

# -----------------------------------------------------------------------------
# TBD -------------------------------------------------------------------------
# -----------------------------------------------------------------------------
12_summarize_aab_timeseries.py
13_summarize_projected_metvars.py

conda deactivate
