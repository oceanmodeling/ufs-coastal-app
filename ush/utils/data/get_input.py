import warnings
from . import get_herbie
from . import get_wget
from . import get_s3

warnings.filterwarnings('ignore')

def download(config, cycle, bbox=None):
    """
    Generic wrapper for downloading data.
    """
    match config['data']['protocol']:
        case 'herbie':
            get_herbie.download(config, cycle, bbox=bbox)
        case 'wget':
            get_wget.download(config, cycle, bbox=bbox)
        case 's3':
            get_s3.download(config, cycle, bbox=bbox)
        case _:
            print('default')
