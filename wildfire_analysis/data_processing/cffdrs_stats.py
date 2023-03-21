"""
Description
-----------
This set of functions calculates annual CFFDRS statistical summaries that 
capture different aspects of extreme fire weather conditions. The four 
statistical summaries are based on Abatzoglou et al (2018):

  - fire weather season length (fwsl)
  - max fire weather anomaly (max)
  - number of days that exceed historical 95th percentile (95d)
  - peak fire weather values for fire season (fs)

References
----------
Abatzoglou, J. T., Williams, A. P., & Barbero, R. (2019). Global emergence of 
anthropogenic climate change in fire weather indices. Geophysical Research 
Letters, 46, 326–336. https://doi.org/10.1029/2018GL080959

Jolly, W., Cochrane, M., Freeborn, P., Holden, Z. A., Brown, T., Williamson, 
G. J., & Bowman, D. M. J. S. (2015). Climate-induced variations in global 
wildfire danger from 1979 to 2013. Nature Communications, 6(1), 7537. 
https://doi.org/10.1038/ncomms8537
"""

import warnings
import xarray as xr

# Filter out warning on all-nan slice operations, expected
warnings.filterwarnings('ignore',
    message='All-NaN slice encountered')

# Maximum anomaly relative to 30-yr climatological average
def _max_calc(ds: xr.Dataset,hst_yr=(1980,2009)) -> xr.Dataset:

    # Get slice for historial reference years
    yr_slice = slice(hst_yr[0],hst_yr[1])

    # Find annual maximum
    ds_annual_max = ds.groupby('time.year').max(dim='time')

    # Find 30-yr average annual maximum
    ds_max_hst_avg = ds_annual_max.sel(year=yr_slice).mean(dim="year")
    
    # Calculate anomaly relative to historical average
    ds_max = ds_annual_max - ds_max_hst_avg

    # Assign a new coordinate to specific the statistical summary, here 'max'
    ds_max = ds_max.assign_coords(coords={'stat': 'max'})

    return ds_max

# Number of days in a given year that exceed the historical 95th percentile
def _ndays_gt_95th(ds: xr.Dataset,hst_yr: tuple=(1980,2009)) -> xr.Dataset:

    # Get slice for historial reference years
    yr_slice = slice('%d-01-01' % hst_yr[0],'%d-12-31' % hst_yr[1])

    # Get historical 95th percentile value for refernce period
    ds_95pct_hst = ds.sel(time=yr_slice).quantile(0.95,dim='time')
    
    # Classify whether each grid cell and day is greater than this historical
    # 95th percentile (True=1) or below it (False=0). This is now of bool 
    # dtype and we can sum the number of days greater than historical value
    # for each year. 
    ds_95pct_rel = ds > ds_95pct_hst
    ds_95d = ds_95pct_rel.groupby('time.year').sum(dim='time')
    ds_95d = ds_95d.reset_coords("quantile",drop=True)

    # Assign a new coordinate to specific the statistical summary, here '95d'
    ds_95d = ds_95d.assign_coords(coords={'stat': '95d'})

    return ds_95d

# Peak fire season value defined using highest 90 moving average value in a 
# given year
def _fs(ds: xr.Dataset) -> xr.Dataset:

    ds_fs = ds.rolling(time=90,center=True).mean()
    ds_fs = ds_fs.groupby('time.year').max()

    # Assign a new coordinate to specific the statistical summary, here 'fs'
    ds_fs = ds_fs.assign_coords(coords={'stat': 'fs'})

    return ds_fs

# Fire weather season length following method from Jolly et al. 2015
def _fwsl(ds: xr.Dataset,hst_yr: tuple=(1980,2009)) -> xr.Dataset:

    yr_slice = slice('%d-01-01' % hst_yr[0],'%d-12-31' % hst_yr[1])

    ds_min = ds.sel(time=yr_slice).min(dim='time')
    ds_max = ds.sel(time=yr_slice).max(dim='time')

    ds_norm = 100.0 * ((ds - ds_min) / (ds_max - ds_min))
    
    ds_fwsl = xr.where(ds_norm > 50.0,1.0,0.0)
    ds_fwsl = ds_fwsl.groupby('time.year').sum()

    # Assign a new coordinate to specific the statistical summary, here 'fwsl'
    ds_fwsl = ds_fwsl.assign_coords(coords={'stat': 'fwsl'})

    return ds_fwsl

def calc_fireweather_stats(
        src_list: list,
        hst_yr: tuple=(1980,2009),
        parallel=True) -> xr.Dataset:    

    ds = xr.open_mfdataset(src_list,parallel=parallel,engine='h5netcdf')

    if parallel:
        ds = ds.chunk(chunks={'time':-1,'lat': 20,'lon': 60})

    ds_max = _max_calc(ds,hst_yr=hst_yr)
    ds_95d = _ndays_gt_95th(ds,hst_yr=hst_yr)
    ds_fs = _fs(ds)
    ds_fwsl = _fwsl(ds,hst_yr=hst_yr)

    ds_to_export = xr.combine_nested([ds_max,ds_95d,ds_fs,ds_fwsl],
                                     concat_dim='stat')
    
    return ds_to_export

if __name__ == '__main__':

    None