import pathlib

import dask
import numpy as np
import xarray as xr
from xclim.core.units import str2pint
from xclim.sdba import QuantileDeltaMapping
from xclim.sdba.processing import jitter_under_thresh

from wildfire_analysis.utils import helpers as h

import warnings
# Filter out warning on all-nan slice operations, expected
warnings.filterwarnings('ignore',
    message='All-NaN slice encountered in interp_on_quantiles')

# Suppress dask warnings on chunk size
dask.config.set({"array.slicing.split_large_chunks": False})    

def same_vals(x):

    return x.count(x[0]) == len(x)

def check_var_names(*args):

    var_names = [h.get_var_names(x)[0] for x in args]

    if not same_vals(var_names):
        raise Exception("Data variables need to be the same in all datasets.")

    return var_names[0]

def same_units(*args):

    units = [str2pint(x.units).units for x in args]

    if not same_vals(units):
        raise Exception("Units need to be the same in all datasets.")

    return None

def dimcheck_and_regrid(ref,hst,sim,regrid='era2gcm'):
  
    ref_shape = ref.shape    
    hst_shape = hst.shape
    sim_shape = sim.shape

    shape_check_1 = same_vals([ref_shape,hst_shape,sim_shape])

    # If datasets are not the same size then regridding needs to be done   
    if not shape_check_1: # If datasets are not the same size ...

        if not any([regrid=='era2gcm',regrid=='gcm2era']):
            raise Exception("Array shapes not equal, need to do regridding and \
                'regrid' argument needs to be either 'era2gcm' or 'gcm2era'")

        if regrid == 'era2gcm':
            
            ref = h.regrid_geodata(ref,hst)

        elif regrid == 'gcm2era':
            
            hst = h.regrid_geodata(hst,ref)
            sim = h.regrid_geodata(sim,ref)

        ref_shape = ref.shape
        hst_shape = ref.shape    
        sim_shape = sim.shape

        # Check to make sure regridding worked and also double checks to make 
        # sure time dims are the same size across datasets
        
        if not same_vals([ref_shape,hst_shape,sim_shape]):
            raise Exception("ref,hst,sim array shapes are not equal! \
                Double check input. Time dimensions need to be same as well.")

    return (ref,hst,sim)                 

def mask_arrays(ref,hst,sim,mask=None):

    # Mask grid cells out of study area
    if mask is not None:
    
        if isinstance(mask,np.ndarray):

            mask_grd = mask.copy()
            del mask

        elif isinstance(mask,pathlib.PosixPath) or isinstance(mask,str):

            mask_grd = h.mask_from_shp(mask,ref)
    
        mask_3d = np.broadcast_to(mask_grd,ref.shape)

        ref = ref.where(mask_3d)
        hst = hst.where(mask_3d)
        sim = sim.where(mask_3d)

    return (ref,hst,sim)

def chunk_data_arrays(ref,hst,sim,frac=0.2):

    # Partition dataset into dask chunks for parallel processing if set to True.
    # Currently set to 20% the size of each dimension, can modify this later to 
    # make it more dynamic. Time dimension cannot be broken up for doing quantile
    # mapping.

    axes = h.get_geoaxes(ref)

    n, m = (ref[axes['X'][0]].size, ref[axes['X'][0]].size)

    ref = ref.chunk(chunks={
        'time':-1,
        'lat': round(n * frac),
        'lon': round(m * frac)
        })

    hst = hst.chunk(chunks={
        'time':-1,
        'lat': round(n * frac),
        'lon': round(m * frac)
        })

    sim = sim.chunk(chunks={
        'time':-1,
        'lat': round(n * frac),
        'lon': round(m * frac)
        })
    
    return (ref,hst,sim)

def quantile_delta_mapping(ref_src,hst_src,sim_src,
    min_thresh = None,
    return_hst=False,
    dask_load=False,
    dask_return=False,
    **kwargs):

    if dask_load is False:
        dask_return = False

    # Read in datasets for reference time period (ref), historical overlap of 
    # gcm (hst), and future simulation/projection period (sim)
    ref = xr.open_mfdataset(
        ref_src,
        engine='h5netcdf',
        parallel=dask_load,
        chunks={'time':365,'lon':-1,'lat':-1}
        )

    hst = xr.open_mfdataset(
        hst_src,
        engine='h5netcdf',
        parallel=dask_load,
        chunks={'time':365,'lon':-1,'lat':-1}
        )

    sim = xr.open_mfdataset(
        sim_src,
        engine='h5netcdf',
        parallel=dask_load,
        chunks={'time':365,'lon':-1,'lat':-1}
        )

    # Check to make sure the variable (e.g. precip) is the same for each dataset
    var = check_var_names(ref,hst,sim)

    # Convert from dataset to dataarray
    ref = ref[var]
    hst = hst[var]
    sim = sim[var]

    # Will raise Exception if not all the same.
    same_units(ref,hst,sim)
    
    # Do regridding so all data arrays are aligned and have the same shape and
    # dimensions
    ref, hst, sim = dimcheck_and_regrid(ref,hst,sim,
        **h.get_kwargs(('regrid',),kwargs))

    # Apply spatial mask, does nothing if 'mask=None'
    ref, hst, sim = mask_arrays(ref,hst,sim,
        **h.get_kwargs(('mask',),kwargs))

    # If working with dask arrays, set chunks so time dimension is not broken up
    # This is a requirement for using sdba.QuantileDeltaMapping
    if dask_load:
        ref, hst, sim = chunk_data_arrays(ref,hst,sim,
            **h.get_kwargs(('frac',),kwargs))

    # Apply uniform random variable if value is less then preset amount. Mainly
    # used for precip (e.g., 0.5 mm/day)
    if min_thresh is not None:

        thresh_str = "%0.3f %s" % (min_thresh,ref.attrs['units'])

        ref = jitter_under_thresh(ref,thresh_str)
        hst = jitter_under_thresh(hst,thresh_str)
        sim = jitter_under_thresh(sim,thresh_str)    

    # Training step in Quantile delta mapping
    QDM = QuantileDeltaMapping.train(ref,hst,
        **h.get_kwargs(('group','nquantiles','kind'),kwargs))        

    # Declare empty tuple to store output
    return_ds = ()

    # Only do historical bias corrections if return_hist=True
    if return_hst:

        # Bias correcting step for hst time period
        hst_ba = QDM.adjust(hst,
            **h.get_kwargs(('interp','extrapolation'),kwargs))

        # Set all jittered values back to 0
        if min_thresh is not None:

            hst_ba = xr.where(hst_ba > min_thresh,hst_ba,0.0)

        hst_ba = hst_ba.rename(var)
        hst_ba = hst_ba.assign_attrs(hst.attrs)

        return_ds = return_ds + tuple([hst_ba])

    # Bias correcting step for projected/simulated time period
    sim_ba = QDM.adjust(sim,
        **h.get_kwargs(('interp','extrapolation'),kwargs))

    # Set all jittered values back to 0
    if min_thresh is not None:

        sim_ba = xr.where(sim_ba > min_thresh,sim_ba,0.0)

    sim_ba = sim_ba.rename(var)
    sim_ba = sim_ba.assign_attrs(sim.attrs)

    return_ds = return_ds + tuple([sim_ba])

    # Export results
    if (not dask_return) & (dask.is_dask_collection(return_ds[0])):

        return tuple([x.compute() for x in return_ds])

    else:

        return return_ds

def main():

    return

if __name__ == '__main__':

    main()