# Import required libraries
from concurrent.futures import process
import sys

import xarray as xr
from tqdm import tqdm

from wildfire_analysis.config import processed_data_dir, gcm_list

standard_dict_file = os.path.join(str(Path(abs_path).parents[0]),"ancillary_data",
    "standard_variable_names.pickle")
with open(standard_dict_file,'rb') as f:
    standard_variable_dict = pickle.load(f)

ffmc_attrs = standard_variable_dict["ffmc"]
dmc_attrs = standard_variable_dict["dmc"]
dc_attrs = standard_variable_dict["dc"]
isi_attrs = standard_variable_dict["isi"]
bui_attrs = standard_variable_dict["bui"]
fwi_attrs = standard_variable_dict["fwi"]

wdir = processed_data_dir

with tqdm(total=N,disable=not verbose) as pbar:

    for i in range(N):

        glob_pattern = os.path.join(src_dir,"*%d*.nc" % yr[i])
        file_list = glob.glob(glob_pattern)

        if len(file_list) == 4:

            ds = xr.open_mfdataset(file_list) #,engine="h5netcdf")

        else:

            ds = xr.load_dataset(file_list) #,engine="h5netcdf")

        vars = list(ds.keys())
        stand_var_list = list()

        for v in range(len(vars)):

            stand_name = ds[vars[v]].attrs["standard_name"]
            stand_var_list.append(stand_name)

            if stand_name == ("air_temperature"):           
                tas = ds[vars[v]].values
                tas[tas == -9999.0] = np.nan

            elif stand_name == ("relative_humidity"):
                hur = ds[vars[v]].values
                hur[hur == -9999.0] = np.nan

            elif stand_name == ("wind_speed"):
                sfcWind = ds[vars[v]].values
                sfcWind[sfcWind == -9999.0] = np.nan

            elif stand_name == ("precipitation"):
                pr = ds[vars[v]].values
                pr[pr == -9999.0] = np.nan

        c = np.count_nonzero(np.isin(stand_var_list,["air_temperature",
            "relative_humidity","wind_speed","precipitation"]))

        if c != 4:
            print("!Not all variables present for CFFDRS calculations.")
            sys.exit(0)

        metvars = np.stack((tas,hur,sfcWind,pr),axis=-1)
        mon = ds.time.dt.month.values

        cffdrs_vals = cffdrs.cffdrs_calc(metvars,mon)    

        cffdrs_ds = xr.Dataset(
                data_vars=
                {"ffmc": (["time","lat","lon"],fwi_vals["ffmc"],ffmc_attrs),
                "dmc": (["time","lat","lon"],fwi_vals["dmc"],dmc_attrs),
                "dc": (["time","lat","lon"],fwi_vals["dc"],dc_attrs),
                "isi": (["time","lat","lon"],fwi_vals["isi"],isi_attrs),
                "bui": (["time","lat","lon"],fwi_vals["bui"],bui_attrs),
                "fwi": (["time","lat","lon"],fwi_vals["fwi"],fwi_attrs),
                },coords=
                {"time": ("time",ds["time"].values),
                "lat": ("lat",ds["lat"].values,ds["lat"].attrs),
                "lon": ("lon",ds["lon"].values,ds["lon"].attrs),
                })

        cffdrs_ds_dt = h.uconvert_time(cffdrs_ds["time"].values,
            "days since 1850-01-01 12:00:00")

        cffdrs_ds = cffdrs_ds.merge({"time": cffdrs_ds_dt},
            overwrite_vars="time")
        cffdrs_ds["time"].attrs["units"] = "days since 1850-01-01 12:00:00"
        cffdrs_ds["time"].attrs["calendar"] = "noleap"

        fn = os.path.basename(file_list[-1])
        fn = fn.split("_")
        fn[0] = "cffdrs"
        fn = "_".join(fn)

        fn = os.path.join(dst_dir,fn)

        cffdrs_ds.to_netcdf(fn,            
            encoding={
                "time": {"dtype": "int","_FillValue": None},
                "lat":  {"dtype": "single","_FillValue": None},
                "lon": {"dtype": "single","_FillValue": None},
                "ffmc": {"dtype": "single","_FillValue": -9999},
                "dmc": {"dtype": "single","_FillValue": -9999},
                "dc": {"dtype": "single","_FillValue": -9999},
                "isi": {"dtype": "single","_FillValue": -9999},
                "bui": {"dtype": "single","_FillValue": -9999},
                "fwi": {"dtype": "single","_FillValue": -9999},
                }) # engine="h5netcdf",
        
        pbar.update() # Update progress bar
