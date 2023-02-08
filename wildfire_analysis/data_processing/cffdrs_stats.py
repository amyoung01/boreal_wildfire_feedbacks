import xarray as xr

def max_calc(ds,hst_yr=(1980,2009)):

    yr_slice = slice(hst_yr[0],hst_yr[1])

    ds_annual_max = ds.groupby('time.year').max(dim='time')
    ds_max_hst_avg = ds_annual_max.sel(year=yr_slice).mean(dim="year")
    ds_max = ds_annual_max - ds_max_hst_avg

    ds_max = ds_max.assign_coords(coords={'stat': 'max'})

    return ds_max

def ndays_gt_95th(ds,hst_yr=(1980,2009)):

    yr_slice = slice(hst_yr[0],hst_yr[1])

    ds_95pct_hst = ds.sel(time=yr_slice).quantile(0.95,dim='time')
    ds_95pct_rel = ds > ds_95pct_hst
    ds_95d = ds_95pct_rel.groupby('time.year').sum(dim='time')
    ds_95d = ds_95d.reset_coords("quantile",drop=True)

    ds_95d = ds_95d.assign_coords(coords={'stat': '95d'})

    return ds_95d

def fs(ds):

    ds_fs = ds.rolling(time=90,center=True).mean()
    ds_fs = ds_fs.groupby('time.year').max()

    ds_fs = ds_fs.assign_coords(coords={'stat': 'fs'})

    return ds_fs

def fwsl(ds,hst_yr=(1980,2009)):

    yr_slice = slice(hst_yr[0],hst_yr[1])

    ds_min = ds.sel(time=yr_slice).min(dim='time')
    ds_max = ds.sel(time=yr_slice).max(dim='time')

    ds_norm = 100.0 * ((ds - ds_min) / (ds_max - ds_min))
    
    ds_fwsl = xr.where(ds_norm > 50.0,1.0,0.0)
    ds_fwsl = ds_fwsl.groupby('time.year').sum()

    ds_fwsl = ds_fwsl.assign_coords(coords={'stat': 'fwsl'})

    return ds_fwsl

def calc_fireweather_stats(src_list,hst_yr=(1980,2009),parallel=False):

    ds = xr.open_mfdataset(src_list,parallel=parallel,engine='h5netcdf')

    ds_max = max_calc(ds,hst_yr=hst_yr)
    ds_95d = ndays_gt_95th(ds,hst_yr=hst_yr)
    ds_fs = fs(ds)
    ds_fwsl = fwsl(ds,hst_yr=hst_yr)

    ds_to_export = xr.combine_nested(
        [ds_max,ds_95d,ds_fs,ds_fwsl],
        concat_dim='stat')
    
    return ds_to_export

def main():

    return None

if __name__ == '__main__':

    main()