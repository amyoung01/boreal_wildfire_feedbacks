#!/bin/bash

# -----------------------------------------------------------------------------
# Machine information
# ProductName:            macOS
# ProductVersion:         13.0.1
# BuildVersion:           22A400
# Architecture:           arm64
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Prerequisties:
# 1. miniconda (conda version 4.12.0) 
# 2. homebrew (3.6.21) to install:
#     - curl 7.84.0
#     - wget 1.21.3
#     - yq v4.30.8
#     - jags 4.3.1
# 3. Python 3.9.15. Required libraries below and listed in requirements.txt:
#     - cdsapi=0.5.1
#     - dask=2022.12.1
#     - gdal=3.6.2
#     - geopandas=0.12.2
#     - numpy=1.23.5
#     - pandas=1.5.2
#     - pyproj=3.4.1
#     - pyyaml=6.0
#     - rasterio=1.3.4
#     - shapely=2.0.0
#     - tqdm=4.64.1
#     - xarray=2022.12.0
#     - xclim=0.40.0
# 4. R (base) 4.2.2. Required libraries:
#     - actuar; Actuarial Functions and Heavy Tailed Distributions (v3.3-1)
#     - car; Companion to Applied Regression (v3.1-1)
#     - data.table; Extension of 'data.frame' (v1.14.6)
#     - fitdistrplus; Fit Parametric Distributions (v1.1-8)
#     - R2jags; Using R to Run 'JAGS' (v0.7-1)
#     - scam; Shape Constrained Additive Models (v1.2-13)
# 5. Login ability to download data from the following sources:
#     - ERA5 Climate Data: https://cds.climate.copernicus.eu/api-how-to
#     - CMIP6 GCM Output: https://esgf-node.llnl.gov/projects/cmip6/
#     - NASA AppEEARS for MODIS datasets: https://appeears.earthdatacloud.nasa.gov
# -----------------------------------------------------------------------------

# Add script directories to current PATH
CWD=$( pwd )
PATH=$PATH:$CWD/bash:$CWD/R:$CWD/scripts

# Create conda env and install required libraries
conda create --name boreal-wildfire-analysis python=3.9.15 r-base=4.2.2

source /opt/anaconda3/etc/profile.d/conda.sh
conda activate boreal-wildfire-analysis

conda install -c conda-forge \
  cdsapi=0.5.1 \
  dask=2022.12.1 \
  gdal=3.6.2 \
  geopandas=0.12.2 \
  numpy=1.23.5 \
  pandas=1.5.2 \
  pyproj=3.4.1 \
  pyyaml=6.0 \
  rasterio=1.3.4 \
  shapely=2.0.0 \
  tqdm=4.64.1 \
  xarray=2022.12.0 \
  xclim=0.40.0
conda install -c r \
  r-essentials \
  r-car=3.1_1 \
  r-data.table=1.14.6

LIBPATH=$( Rscript -e "cat(.libPaths())" )
Rscript --vanilla R/install_req_pkgs.R $LIBPATH

###############################################################################
# TODO: Need to figure out how to install 'rjags' and 'R2jags' in a specific
# or new conda environment.
###############################################################################

# To generate token needed for MOD44B download see <INSERT URL>
EARTHDATA_TOKEN="[NEED TO INSERT EARTHDATA LOGIN TOKEN HERE]"

# -----------------------------------------------------------------------------
# Download datasets -----------------------------------------------------------
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
# scripts in the repository, but we do provide a text file for each netcdf
# downloaded containing all the metadata for each file. These text files
# are provided in data/ancillary/list_of_cmip6

download_cmip6.sh

# Download ERA5 datasets using a set of python scripts wrapped in shell script.
# Also run script to convert these ERA5 netcdf files from NetCDF3 to NetCDF4.
python bash/z_era5_download_scripts/download_era5.py
convert_era5_to_netcdf4.sh

# -----------------------------------------------------------------------------
# Organize datasets for processing:
#   Re-organize and process ERA5 datasets to daily values of desired 
#   variables
# -----------------------------------------------------------------------------
01_process_era5.py --verbose
02_process_cmip6.py --verbose
03_modify_ecoregion_shapefile.py

# Also, project ecroregion shapefile from geographic to projected reference 
# system using gdal
ogr2ogr

# -----------------------------------------------------------------------------
# Bias correct GCM data -------------------------------------------------------
# -----------------------------------------------------------------------------
04_bias_correct_gcms.py --verbose

# -----------------------------------------------------------------------------
# CFFDRS Calculations ---------------------------------------------------------
# -----------------------------------------------------------------------------
05_calculate_cffdrs.py
06_calculate_cffdrs_summaries.py
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
