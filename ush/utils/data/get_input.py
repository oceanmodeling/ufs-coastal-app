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

#    'data': {'protocol': 'herbie', 'source': 'hrrr', 'length': 3, 'fxx': 0, 'subset': True, 'target_directory': 'INPUT'}

#{'taxmode': 'limit', 'mapalgo': 'redist', 'tinterpalgo': 'linear', 'readmode': 'single', 'dtlimit': 1.5, 'stream_offset': 0, 'yearAlign': 2024, 'yearFirst': 2024, 'yearLast': 2024, 'stream_vectors': 'null', 'stream_lev_dimname': 'null', 'stream_data_variables': ['u10 Sa_u10m', 'v10 Sa_v10m', 'mslma Sa_pslv'], 'data': {'protocol': 'herbie', 'source': 'hrrr', 'length': 3, 'fxx': 0, 'subset': True, 'target_directory': 'INPUT'}, 'target_directory': 'INPUT', 'stream_data_files': ['INPUT/combined_datm_stream01.nc'], 'stream_mesh_file': ['INPUT/mesh_datm_stream01.nc']}
#{'taxmode': 'limit', 'mapalgo': 'bilinear', 'tinterpalgo': 'linear', 'readmode': 'single', 'dtlimit': 1.5, 'stream_offset': 0, 'yearAlign': 2024, 'yearFirst': 2024, 'yearLast': 2024, 'stream_vectors': 'null', 'stream_lev_dimname': 'null', 'stream_data_variables': ['sst So_t'], 'data': {'protocol': 's3', 'endpoint': 'noaa-ufs-regtests-pds', 'files': ['input-data-20221101/FV3_fix_tiled/C96/C96.maximum_snow_albedo.tile1.nc']}, 'target_directory': 'INPUT', 'stream_data_files': ['INPUT/combined_docn_stream02.nc'], 'stream_mesh_file': ['INPUT/mesh_docn_stream02.nc']}

