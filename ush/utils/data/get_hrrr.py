import os
from datetime import datetime
from datetime import timedelta
from herbie import Herbie
import xarray as xr
import logging
import warnings

warnings.filterwarnings('ignore')
CYCLING_INTERVAL = timedelta(seconds=3600)
EPSILON = timedelta(seconds=5)
searchString = '(:[U|V]GRD:10 m|:MSLMA:)'
logger = logging.getLogger('hrrr')

def download(cfg, cycle, bbox, combine=False, output_dir='./'):
    now = cycle
    end = cycle + timedelta(hours=cfg['length'])
    date_set = set()
    while now < end + EPSILON:
        date_set.add(now.strftime('%Y-%m-%d %H:%M'))
        now += CYCLING_INTERVAL
    date_list = list(date_set)
    date_list.sort()
    if not date_list:
        logger.warning('Nothing to do! Exiting.')
        exit(1)
    file_set = set()
    for date in date_list:
        try:
            ofile = get(date, cfg['fxx'], bbox, output_dir)
            file_set.add(ofile)
        except Exception as ex:
            logger.error(f'Download failed for {date}: {ex}', exc_info=ex)
    file_list = list(file_set)
    file_list.sort()
    if combine:
        ds = xr.open_mfdataset(file_list, combine='nested', concat_dim='time')
        ofile = os.path.join(output_dir, 'combined.nc')
        ds.to_netcdf(ofile)
        return ofile
    else:
        return file_list

def get(date, fxx, bbox, output_dir):
    H = Herbie(date=date, model='hrrr', product='sfc', fxx=0, save_dir=output_dir)
    lfile = H.download(search=searchString)
    if os.path.isfile(lfile):
        dirname = os.path.dirname(lfile)
        ofile = os.path.join(dirname, datetime.strptime(date, '%Y-%m-%d %H:%M').strftime('%Y%m%d_%Hz') + '.nc')
        ds = xr.open_dataset(lfile, engine='cfgrib')
        bbox_ext = [bbox[0] * 0.95, bbox[1] * 1.1, bbox[2] * 0.95, bbox[3] * 1.1]
        ds_subset = ds.where((ds.latitude > bbox_ext[2]) & (ds.latitude < bbox_ext[3]) & (ds.longitude > bbox_ext[0]) & (ds.longitude < bbox_ext[1]), drop=True)
        ds_subset.to_netcdf(ofile)
    return ofile
