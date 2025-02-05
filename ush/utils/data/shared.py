import numpy as np
import xarray as xr
import logging
import warnings

warnings.filterwarnings('ignore')

def bbox_mask(ds, bbox):
    """
    Calcuates mask associated with given bounding box and data file
    """
    # Create mask based on given box and coordinates
    min_lon, min_lat, max_lon, max_lat = bbox
    logging.info('Subset data using bounding box: min_lon = %f, min_lat = %f, max_lon = %f, max_lat = %f', min_lon, min_lat, max_lon, max_lat)
    if 'lat' in ds.coords:
        lat = ds['lat']
    elif 'latitude' in  ds.coords:
        lat = ds['latitude']
    if 'lon' in ds.coords:
        lon = ds['lon']
    elif 'longitude' in ds.coords:
        lon = ds['longitude']
    mask = (lat >= min_lat) & (lat <= max_lat) & (lon >= min_lon) & (lon <= max_lon)
    # Find indexes that match with given mask and modify mask
    indx = np.argwhere(mask.values)
    istart = indx[:,0].min()-1
    iend = indx[:,0].max()+1
    jstart = indx[:,1].min()-1
    jend = indx[:,1].max()+1
    mask[istart:iend+1,jstart:jend+1] = True
    # Return mask
    return(mask)
