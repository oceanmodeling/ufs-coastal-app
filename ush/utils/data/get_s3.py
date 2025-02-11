import os
import warnings
import logging
try:
    import boto3
    import botocore.exceptions
    from botocore import UNSIGNED
    from botocore.client import Config
except ImportError:
    logging.error('Module boto3 not found.')
try:
    import hashlib
except ImportError:
    logging.error('Module hashlib not found.')

#import subprocess
#import xarray as xr
#from pathlib import Path
#from . import shared

warnings.filterwarnings('ignore')

def download(config, cycle, bbox=[]):
    """
    Download data from S3 bucket 
    """
    # Create an S3 access object, config option allows accessing anonymously
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    # Get target directory
    target_dir = config['data']['target_directory']
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    # Get other options
    end_point = config['data']['end_point']
    # Loop over files
    file_list = []
    for fn in config['data']['files']:
        flag = False
        local_fn = os.path.join(target_dir, os.path.basename(fn))
        # Try to fine checksum of remote file on s3 bucket
        md5sum_remote = None
        try:
            md5sum_remote = s3.head_object(Bucket=end_point, Key=fn)['ETag'][1:-1]
        except botocore.exceptions.ClientError as e:
            logging.info('Skip checking md5sum for {} since the object does not exist in {}!'.format(fn, end_point))
            continue
        # Try to find checksum of local file
        md5sum_local = None
        if os.path.exists(local_fn):
            md5sum_local = hashlib.md5(open(local_fn,'rb').read()).hexdigest()
            # Compare checksums
            if md5sum_remote != md5sum_local:
                logging.warn('Checksums for remote and local file are not same! Force to download {}'.format(fn))
                flag = True
            else:
                logging.info('Checksums for remote and local file are matching. Skip downloading {}'.format(fn))
        else:
            flag = True
        # Download file
        if flag:
            s3.download_file(Bucket=end_point, Key=fn, Filename=local_fn)





    ## Check configuration
    #combine = True
    #print(config["data"].keys())
    #if 'combine' in config['data'].keys():
    #    combine = config['data']['combine']
    ## Get target directory
    #target_dir = config['data']['target_directory']
    #if not os.path.isdir(target_dir):
    #    os.mkdir(target_dir)
    ## Loop over files
    #file_list = []
    #for fn in config['data']['files']:
    #    local_fn = os.path.join(target_dir, os.path.basename(fn))
    #    # Retrieve files with wget command
    #    end_point = config['data']['end_point']
    #    cmd = f"wget --no-verbose --no-check-certificate -c {end_point}:{fn}"
    #    logging.debug("Running: %s", cmd)
    #    result = subprocess.check_call(cmd, cwd=Path(local_fn).parent, shell=True)
    #    # Subset file if it is required
    #    if bbox:
    #        # Open dataset
    #        root, ext = os.path.splitext(local_fn)
    #        engine = 'cfgrib' if ext == '.grb' or ext == '.grib' else 'netcdf4'
    #        ds = xr.open_dataset(local_fn, engine=engine)
    #        # Subset data and write to a new file
    #        mask = shared.bbox_mask(ds, bbox)
    #        clipped_ds = ds.where(mask, drop=True)
    #        ofile = local_fn.replace(ext, '_sub'.join(ext))
    #        clipped_ds.to_netcdf(ofile)
    #        os.rename(ofile, local_fn)
    #    # Add file to list
    #    file_list.append(local_fn)
    ## Combine files
    #if combine and not os.path.exists(config['stream_data_files'][0]):
    #    logging.info('List of files that will be combined: %s', ' '.join(map(str, file_list)))
    #    file_list.sort()
    #    ds = xr.open_mfdataset(file_list, combine='nested', concat_dim='time', coords='minimal', compat='override', engine='netcdf4')
    #    ds.to_netcdf(config['stream_data_files'][0])
    #    return([config['stream_data_files'][0]])
    #else:
    #    return(file_list)
