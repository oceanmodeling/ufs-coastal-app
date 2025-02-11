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

def download(config, cycle, bbox=[]):
    # Check configuration and set defaults
    overwrite = False
    if 'overwrite' in config.keys():
        overwrite = config['overwrite']

    combine = True
    if 'combine' in config.keys():
        combine = config['combine']

    source = 'hrrr'
    if 'source' in config.keys():
        source = config['source'].lower()

    fxx = 0
    if 'fxx' in config.keys():
        fxx = config['fxx']

    length = 24
    if 'length' in config.keys():
        length = config['length']

    # Set time step for given dataset
    if source == 'hrrr':
        CYCLING_INTERVAL = timedelta(seconds=3600)
    elif source == 'gfs':
        CYCLING_INTERVAL = timedelta(seconds=21600)

    # Update length
    # NB: This is CDEPS specific and adds one time step more at the end to allow performing temporal interpolation
    length = length+CYCLING_INTERVAL.seconds//3600

    # Additional check for given configuration
    if source == 'gfs' and fxx == 0 and length < 6:
        logging.error('GFS is initialized every 6-hours. The lenght %d needs to be multiples of 6 !!!', length)
        sys.exit()

    # Create lists of dates that needs to be downloaded
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

    # Loop over dates and download them
    file_set = set()
    for date in date_list:
        logging.info("Getting data for %s", date)
        try:
            target_directory = config['data']['target_directory']
            ofile = get(date, source, fxx, bbox, overwrite, target_directory)
            file_set.add(ofile)
        except Exception as ex:
            logging.error('Download failed for %s: %s', date, str(ex))

    # Combine files
    file_list = list(file_set)
    file_list.sort()
    if combine:
        if not os.path.isfile(config['stream_data_files'][0]):
            logging.info('List of files that will be combined: %s', ' '.join(map(str, file_list)))
            ds = xr.open_mfdataset(file_list, combine='nested', concat_dim='time', coords='minimal', compat='override', engine='netcdf4')
            ds.to_netcdf(config['stream_data_files'][0])
        else:
            logging.info('Skip combining files since %s is already created.', config['stream_data_files'][0])

def get(date, source, fxx, bbox, overwrite, output_dir):
    # Create object
    if source == 'hrrr':
        H = Herbie(date=date, model='hrrr', product='sfc', fxx=fxx, save_dir=output_dir, overwrite=overwrite)
    elif source == 'gfs':
        H = Herbie(date=date, model='gfs', product='pgrb2.0p25', fxx=fxx, save_dir=output_dir, overwrite=overwrite)

    # Set search string
    searchString = '(:[U|V]GRD:10 m|:MSLMA:)'
    if source == 'gfs':
        searchString = '(:[U|V]GRD:10 m above ground|:PRMSL:)'

    # Download data
    if (H.find_grib() is not None):
        lfile = H.download(search=searchString, overwrite=overwrite)
    else:
        logging.error('Requested file could not found! Exiting')
        sys.exit()

    # Check the file and subset it if it is requested
    if os.path.isfile(lfile):
        dirname = os.path.dirname(lfile)
        ofile = os.path.join(dirname, datetime.strptime(date, '%Y-%m-%d %H:%M').strftime('%Y%m%d_%Hz') + '.nc')
        if not os.path.isfile(ofile) or overwrite:
            # Load data
            ds = xr.open_dataset(lfile, engine='cfgrib')
            # Subset it if it is requested
            if bbox:
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

                # Subset data and write to a new file
                clipped_ds = ds.where(mask, drop=True)
                clipped_ds.to_netcdf(ofile)

    return ofile

#if __name__ == '__main__':
#    sys.exit(main())
