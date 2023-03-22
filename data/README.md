
**Data directory**
---
- **ancillary**
- **raw**  
    - This directory hosts all the downloaded datasets. These data were not changed.
    The downloaded datasets are listed here:
        - **CMIP6**: output from four different GCMs (CNRM-CM6-1-HR, EC-Earth3-Veg, 
        MPI-ESM1-2-HR, MRI-ESM2-0) were obtained from several different nodes 
        on the [ESGF data portal](https://esgf.llnl.gov). The wget scripts
        listing all the files downloaded are available in the ancillary data
        directory.  
        - **ERA5**: historical meteorological data from 1979-2020 was obtained
        from the E  
        - **MOD44B**:  
        - **Fire**:
            - Alaska Large Fire Database
            - Canada National Fire Database
        - **Ecoregions**: 
- **processed**  
    - This directory hosts all intermediary and final data products prior to 
    being summarized in data tables.  
- **dataframes**
    - This directory hosts all the summarized data products into data tables.  
        - *annual_area_burned.csv*: summarizes historical annual area burned for
        each ecoregion from 1950-2020
        - annual statistical summaries of different CFFDRS fire weather 
        indices/metrics. Summaries are based on those described in 
        [Abatzoglou et al. 2018](https://doi.org/10.1029/2018GL080959)  
            - *cffdrs-stats_era5_1979-2020.csv*
            - *cffdrs-stats_CNRM-CM6-1-HR_1980-2099.csv*
            - *cffdrs-stats_EC-Earth3-Veg_1980-2099.csv*  
            - *cffdrs-stats_MPI-ESM1-2-HR_1980-2099.csv*
            - *cffdrs-stats_MRI-ESM2-0_1980-2099.csv*
        - *aab_projected_timeseries.csv*: 

The data directory hosts all the data downloaded and generated through this 
analysis. The structure is as follows:  

```
data
├── ancillary
├── dataframes
├── model_results
│   └── projected_area_burned
├── processed
│   ├── cffdrs
│   │   ├── cffdrs_stats
│   │   ├── cmip6
│   │   │   ├── CNRM-CM6-1-HR
│   │   │   ├── EC-Earth3-Veg
│   │   │   ├── MPI-ESM1-2-HR
│   │   │   └── MRI-ESM2-0
│   │   └── era5
│   ├── climate
│   │   ├── cmip6
│   │   │   ├── CNRM-CM6-1-HR
│   │   │   │   └── bias_corrected
│   │   │   ├── EC-Earth3-Veg
│   │   │   │   └── bias_corrected
│   │   │   ├── MPI-ESM1-2-HR
│   │   │   │   └── bias_corrected
│   │   │   └── MRI-ESM2-0
│   │   │       └── bias_corrected
│   │   └── era5
│   ├── ecoregions
│   ├── fire
│   │   ├── rasters
│   │   └── shapefiles
│   └── veg
│       └── mod44b
└── raw
    ├── climate
    │   ├── cmip6
    │   │   ├── CNRM-CM6-1-HR
    │   │   ├── EC-Earth3-Veg
    │   │   ├── MPI-ESM1-2-HR
    │   │   └── MRI-ESM2-0
    │   └── era5    
    ├── ecoregions
    │   └── official
    ├── fire
    │   ├── Alaska
    │   └── Canada
    └── veg
        └── mod44b

```


