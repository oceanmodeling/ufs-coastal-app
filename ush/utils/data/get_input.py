import sys
import logging
from . import get_herbie
from . import get_wget
from . import get_s3

def download(config, cycle, bbox=None):
    """
    Generic wrapper for downloading data.
    """
    protocol = config['data']['protocol']
    if protocol == 'herbie':
        get_herbie.download(config, cycle, bbox=bbox)
    elif protocol == 'wget':
        get_wget.download(config, cycle, bbox=bbox)
    elif protocol == 's3':
        get_s3.download(config, cycle, bbox=bbox)
    else:
        logging.error("Given protocol %s is not supported!", protocol)
        sys.exit()
