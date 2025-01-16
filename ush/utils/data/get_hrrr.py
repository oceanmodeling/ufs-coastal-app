import os
import sys
from datetime import datetime
from datetime import timedelta
from herbie import Herbie
import numpy as np
import xarray as xr
import logging
import warnings

warnings.filterwarnings('ignore')
EPSILON = timedelta(seconds=5)

def download(opts, cycle, bbox=[], combine=False, output_dir='./'):
    # check configuration
    overwrite = False
    if 'overwrite' in opts.keys():
        overwrite = opts['overwrite']

    source = 'hrrr'
    if 'source' in opts.keys():
        source = opts['source'].lower()

    fxx = 0
    if 'fxx' in opts.keys():
        fxx = opts['fxx']

    length = 24
    if 'length' in opts.keys():
        length = opts['length']

    # set interval
    CYCLING_INTERVAL = timedelta(seconds=3600)
    if source == 'gfs':
        CYCLING_INTERVAL = timedelta(seconds=21600)

    # update length (one time step more at the end to allow CDEPS to perform temporal interpolation
    length = length+CYCLING_INTERVAL.seconds//3600

    # check given configuration
    if source == 'gfs' and fxx == 0 and length < 6:
        logging.error('GFS is initialized every 6-hours. The lenght %d needs to be multiples of 6 !!!', length)
        sys.exit()

    # create lists of dates that needs to be downloaded
    now = cycle
    end = cycle + timedelta(hours=length)
    date_set = set()
    while now < end + EPSILON:
        date_set.add(now.strftime('%Y-%m-%d %H:%M'))
        now += CYCLING_INTERVAL
    date_list = list(date_set)
    date_list.sort()
    if not date_list:
        logging.warning('Nothing to do! Exiting.')
        sys.exit()

    logging.info('List of dates that will be retrieved: %s', ', '.join(map(str, date_list)))

    # loop over dates and download them
    file_set = set()
    for date in date_list:
        logging.info("Getting data for %s", date)
        try:
            ofile = get(date, source, fxx, bbox, overwrite, output_dir)
            file_set.add(ofile)
        except Exception as ex:
            logging.error('Download failed for %s: %s', date, str(ex))

    # combine files
    file_list = list(file_set)
    file_list.sort()
    if combine:
        logging.info('List of files that will be combined: %s', ' '.join(map(str, file_list)))
        ds = xr.open_mfdataset(file_list, combine='nested', concat_dim='time', coords='minimal', compat='override', engine='netcdf4')
        ofile = os.path.join(output_dir, 'combined.nc')
        ds.to_netcdf(ofile)
        return ofile
    else:
        return file_list

def get(date, source, fxx, bbox, overwrite, output_dir):
    # download data
    if source == 'hrrr':
        H = Herbie(date=date, model='hrrr', product='sfc', fxx=fxx, save_dir=output_dir)
    elif source == 'gfs':
        H = Herbie(date=date, model='gfs', product='pgrb2.0p25', fxx=fxx, save_dir=output_dir)

    # set search string
    searchString = '(:[U|V]GRD:10 m|:MSLMA:)'
    if source == 'gfs':
        searchString = '(:[U|V]GRD:10 m above ground|:PRMSL:)'

    # check data
    if (H.find_grib() is not None):
        lfile = H.download(search=searchString, overwrite=overwrite)
    else:
        logging.error('Requested file could not found! Exiting')
        sys.exit()

    # check the file and subset it if it is requested
    if os.path.isfile(lfile):
        dirname = os.path.dirname(lfile)
        ofile = os.path.join(dirname, datetime.strptime(date, '%Y-%m-%d %H:%M').strftime('%Y%m%d_%Hz') + '.nc')
        if not os.path.isfile(ofile) or overwrite:
            # load data
            ds = xr.open_dataset(lfile, engine='cfgrib')
            # subset it if it is requested
            if not bbox:
                logging.info('Skip subsetting data ...')
            else:
                # create mask based on given box and coordinates
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

                # find indexes that match with given mask and modify mask
                indx = np.argwhere(mask.values)
                istart = indx[:,0].min()-1
                iend = indx[:,0].max()+1
                jstart = indx[:,1].min()-1
                jend = indx[:,1].max()+1
                mask[istart:iend+1,jstart:jend+1] = True

                # subset data and write to a new file
                clipped_ds = ds.where(mask, drop=True)
                clipped_ds.to_netcdf(ofile)
        else:
            logging.info('%s is found! Skip subsetting data ...', ofile)

    return ofile
