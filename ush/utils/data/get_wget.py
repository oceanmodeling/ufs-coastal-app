import os
import warnings
import logging
import subprocess
import xarray as xr
from pathlib import Path
from . import shared

warnings.filterwarnings('ignore')

def download(config, cycle, bbox=[]):
    """
    Download data using wget command
    """
    # Check configuration
    combine = True
    print(config["data"].keys())
    if 'combine' in config['data'].keys():
        combine = config['data']['combine']
    # Get target directory
    target_dir = config['data']['target_directory']
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    # Loop over files
    file_list = []
    for fn in config['data']['files']:
        local_fn = os.path.join(target_dir, os.path.basename(fn))
        # Retrieve files with wget command
        end_point = config['data']['end_point']
        cmd = f"wget --no-verbose --no-check-certificate -c {end_point}:{fn}"
        logging.debug("Running: %s", cmd)
        result = subprocess.check_call(cmd, cwd=Path(local_fn).parent, shell=True)
        # Subset file if it is required
        if bbox:
            # Open dataset
            root, ext = os.path.splitext(local_fn)
            engine = 'cfgrib' if ext == '.grb' or ext == '.grib' else 'netcdf4'
            ds = xr.open_dataset(local_fn, engine=engine)
            # Subset data and write to a new file
            mask = shared.bbox_mask(ds, bbox)
            clipped_ds = ds.where(mask, drop=True)
            ofile = local_fn.replace(ext, '_sub'.join(ext))
            clipped_ds.to_netcdf(ofile)
            os.rename(ofile, local_fn)
        # Add file to list
        file_list.append(local_fn)
    # Combine files
    if combine and not os.path.exists(config['stream_data_files'][0]):
        logging.info('List of files that will be combined: %s', ' '.join(map(str, file_list)))
        file_list.sort()
        ds = xr.open_mfdataset(file_list, combine='nested', concat_dim='time', coords='minimal', compat='override', engine='netcdf4')
        ds.to_netcdf(config['stream_data_files'][0])
        return([config['stream_data_files'][0]])
    else:
        return(file_list)
