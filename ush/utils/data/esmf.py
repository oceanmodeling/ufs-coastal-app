from pathlib import Path
import logging
try:
    import os
    import sys
    import numpy as np
    import xarray as xr
    import dask.array as da
    import dask.dataframe as dd
    import subprocess
    from datetime import datetime
except ImportError as ie:
    logging.error(str(ie))
    sys.exit()

def create_grid_definition(input_file, output_file='mesh.nc', mask_var=None, ff='scrip', output_dir='./'):
    """
    Create grid definition file in SCRIP or ESMF Mesh format
    """
    # Open input file
    if os.path.isfile(input_file):
        ds = xr.open_dataset(input_file, mask_and_scale=False, decode_times=False)
    else:
        logging.error("Input file %s could not find!", input_file)
        sys.exit()

    # Set output file name
    if os.path.isabs(output_file):
        ofile = output_file
    else:
        ofile = os.path.join(output_dir, output_file)

    # Get coordinate information
    if 'longitude' in ds.keys():
        xc = ds['longitude']
        xc = xc.rename({'longitude': 'x'})
    elif 'lon' in ds.keys():
        xc = ds['lon']
        xc = xc.rename({'lon': 'x'})
    else:
        xc = ds['geolon']
        xc = xc.rename({'geolon': 'x'})
    if 'latitude' in ds.keys():
        yc = ds['latitude']
        yc = yc.rename({'latitude': 'y'})
    elif 'lat' in ds.keys():
        yc = ds['lat']
        yc = yc.rename({'lat': 'y'})
    else:
        yc = ds['geolat']
        yc = xc.rename({'geolat': 'y'})

    # Process coordinate information if it is required
    rank = len(xc.dims)
    if rank == 1: # regular lat-lon
        # Convert to 2d
        nx = xc.size
        ny = yc.size
        xc = xc.expand_dims(dim={'y': ny}).to_numpy()
        yc = yc.expand_dims(dim={'x': nx}).transpose().to_numpy()
    else:
        xc = xc.to_numpy()
        yc = yc.to_numpy()

    # Check file
    if not os.path.isfile(ofile):
        # Get mask information
        if mask_var:
            mc = np.ndarray.flatten(ds[mask_var].to_numpy())
        else:
            mc = np.ones(xc.size, dtype=np.int32)

        # Calculate corner coordinates
        xc_1, yc_1, xo_2, yo_2 = calc_corners(xc, yc)

        # Write to file 
        if ff == 'mesh':
            fn = to_scrip(xc_1, yc_1, xo_2, yo_2, mc, xc.shape[::-1], output_dir=os.path.dirname(ofile))
            ofile = scrip_to_mesh(fn, output_file=ofile, output_dir=output_dir)
        else:
            ofile = to_scrip(xc_1, yc_1, xo_2, yo_2, mc, xc.shape[::-1], output_dir=output_dir)

    return({'output_file': ofile, 'shape': xc.shape[::-1]})

def to_scrip(xc, yc, xo, yo, mc, dims, output_file='scrip.nc', output_dir='./'):
    """
    Writes grid in SCRIP format
    """

    # Create new dataset in SCRIP format
    out = xr.Dataset()

    # Fill with data
    out['grid_dims'] = xr.DataArray(np.array(dims, dtype=np.int32), dims=('grid_rank',))
    out['grid_center_lon'] = xr.DataArray(xc, dims=('grid_size'), attrs={'units': 'degrees'})
    out['grid_center_lat'] = xr.DataArray(yc, dims=('grid_size'), attrs={'units': 'degrees'})
    out['grid_corner_lon'] = xr.DataArray(xo, dims=('grid_size','grid_corners'), attrs={'units': 'degrees'}).astype(dtype=np.float64, order='F')
    out['grid_corner_lat'] = xr.DataArray(yo, dims=('grid_size','grid_corners'), attrs={'units': 'degrees'}).astype(dtype=np.float64, order='F')
    out['grid_imask'] = xr.DataArray(mc, dims=('grid_size'), attrs={'units': 'unitless'})

    # Force no '_FillValue' if not specified
    for v in out.variables:
        if '_FillValue' not in out[v].encoding:
            out[v].encoding['_FillValue'] = None    

    # Add global attributes
    out.attrs = {'title': 'Grid with {} size'.format('x'.join(list(map(str,dims)))),
                 'created_by': os.path.basename(__file__),
                 'date_created': '{}'.format(datetime.now()),
                 'conventions': 'SCRIP'}

    # Write dataset
    ofile = os.path.join(output_dir, output_file)
    out.to_netcdf(ofile)
    return(ofile)

def scrip_to_mesh(input_file, output_file='mesh.nc', output_dir='./'):
    """
    Convert scrip.nc to ESMF mesh format using ESMF_Scrip2Unstruct tool
    """
    # Set output file name
    if os.path.isabs(output_file):
        ofile = output_file
    else:
        ofile = os.path.join(output_dir, output_file)

    # Check ESMFMKFILE environment variable to find out location of executable
    if os.environ['ESMFMKFILE']:
        # Open file and parse it
        with open(os.environ['ESMFMKFILE']) as f:
            bindir = [x.strip().split('=')[1] for x in f.readlines() if 'ESMF_APPSDIR' in x]
            # Run command
            if bindir:
                exe = Path(bindir[0], 'ESMF_Scrip2Unstruct')
                log = Path(ofile).parent / "mesh.log"
                cmd = f"{exe} {input_file} {ofile} 0 >{log} 2>&1"                
                #logging.debug("Running: %s", cmd)
                print("Running: %s", cmd)
                result = subprocess.check_call(cmd, cwd=Path(ofile).parent, shell=True)

    return(ofile)

def calc_corners(xc, yc, delta=0.25):
    """
    Calculate corner coordinates by averaging neighbor cells
    It follows the approach initially developed by NCL and made
    available through calc_SCRIP_corners_noboundaries() call
    """

    # Get sizes of original array
    ny, nx = xc.shape

    # Extend array that stores center coordinates
    xc_ext = np.pad(xc, ((1,1), (1,1)), constant_values=(0, 0))
    yc_ext = np.pad(yc, ((1,1), (1,1)), constant_values=(0, 0))

    # Get sizes, extended array
    ny_ext, nx_ext = xc_ext.shape

    # Fill missing part of expanded array
    # Bottom row, minus corners (left side in data)
    xc_ext[1:ny_ext-1,0] = mirrorP2P(xc[:,1], xc[:,0])
    yc_ext[1:ny_ext-1,0] = mirrorP2P(yc[:,1], yc[:,0])

    # Top, minus corners (right side in data)
    xc_ext[1:ny_ext-1,nx_ext-1] = mirrorP2P(xc[:,nx-2], xc[:,nx-1])
    yc_ext[1:ny_ext-1,nx_ext-1] = mirrorP2P(yc[:,nx-2], yc[:,nx-1])

    # Left, minus corners (top side in data)
    xc_ext[0,1:nx_ext-1] = mirrorP2P(xc[1,:], xc[0,:])
    yc_ext[0,1:nx_ext-1] = mirrorP2P(yc[1,:], yc[0,:])

    # Right, minus corners (bottom side in data)
    xc_ext[ny_ext-1,1:nx_ext-1] = mirrorP2P(xc[ny-2,:], xc[ny-1,:])
    yc_ext[ny_ext-1,1:nx_ext-1] = mirrorP2P(yc[ny-2,:], yc[ny-1,:])

    # Lower left corner (upper left corner in data)
    xc_ext[0,0] = mirrorP2P(xc[1,1], xc[0,0])
    yc_ext[0,0] = mirrorP2P(yc[1,1], yc[0,0])

    # Upper right corner (lower right corner in data)
    xc_ext[ny_ext-1,nx_ext-1] = mirrorP2P(xc[ny-2,nx-2], xc[ny-1,nx-1])
    yc_ext[ny_ext-1,nx_ext-1] = mirrorP2P(yc[ny-2,nx-2], yc[ny-1,nx-1])

    # Lower right corner (upper right corner in data)
    xc_ext[0,nx_ext-1] = mirrorP2P(xc[1,nx-2], xc[0,nx-1])
    yc_ext[0,nx_ext-1] = mirrorP2P(yc[1,nx-2], yc[0,nx-1])

    # Upper left corner (lower left corner in data)
    xc_ext[ny_ext-1,0] = mirrorP2P(xc[ny-2,1], xc[ny-1,0])
    yc_ext[ny_ext-1,0] = mirrorP2P(yc[ny-2,1], yc[ny-1,0])

    # TODO: need to add code for boundary corners if they go over

    # The cell center of the extended grid, which
    # would be the corner coordinates for the original grid
    xo = xc_ext[:,1:nx_ext]+xc_ext[:,0:nx_ext-1]
    xo = delta*(xo[1:ny_ext,:]+xo[0:ny_ext-1,:])
    yo = yc_ext[:,1:nx_ext]+yc_ext[:,0:nx_ext-1]
    yo = delta*(yo[1:ny_ext,:]+yo[0:ny_ext-1,:])

    # Create flattened version of corner coordinates
    kernel = np.array([[1,1], [1,1]])
    xo = arrays_from_kernel(xo, kernel).reshape(ny,nx,-1).reshape(-1,kernel.size)
    xo = xo[:,[0, 1, 3, 2]]
    yo = arrays_from_kernel(yo, kernel).reshape(ny,nx,-1).reshape(-1,kernel.size)
    yo = yo[:,[0, 1, 3, 2]]

    # Return flatten arrays
    return(np.ndarray.flatten(xc),
           np.ndarray.flatten(yc),
           xo,
           yo)

def mirrorP2P(p1, p0):
    """
    This functions calculates the mirror of p1 with respect to po
    """
    dVec = p1-p0
    return(p0-dVec)

def arrays_from_kernel(arr, kernel):
    windows = sliding_window(arr, kernel.shape)
    return np.where(kernel, windows, 0)

def sliding_window(data, win_shape, **kwargs):
    assert data.ndim == len(win_shape)
    shape = tuple(dn - wn + 1 for dn, wn in zip(data.shape, win_shape)) + win_shape
    strides = data.strides * 2
    return np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides, **kwargs)
