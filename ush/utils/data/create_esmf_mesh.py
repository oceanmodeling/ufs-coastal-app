try:
    import os
    import sys
    from datetime import datetime
    import numpy as np
    import xarray as xr
except ImportError as ie:
    sys.stderr.write(str(ie))
    exit(2)

def mirrorP2P(p1, p0):
    """
    This functions calculates the mirror of p1 with respect to po
    """
    dVec = p1-p0
    return(p0-dVec)

def to_scrip(fin, mask_var=None, fout='scrip.nc'):
    """
    Writes grid in SCRIP grid definition file format
    """

    # Open input file
    if os.path.isfile(fin):
        ds = xr.open_dataset(fin, mask_and_scale=False, decode_times=False)
    else:
        print('Input file could not find!')
        exit(2)

    # Get coordinate information
    xc = ds['longitude']
    xc = xc.rename({'longitude': 'x'})
    yc = ds['latitude']
    yc = yc.rename({'latitude': 'y'})

    # Process coordinate information if it is required
    rank = len(xc.dims)
    if rank == 1: # regular lat-lon
        # Convert to 2d
        nx = xc.size
        ny = yc.size
        xc = xc.expand_dims(dim={'y': ny}).to_numpy()
        yc = yc.expand_dims(dim={'x': nx}).transpose().to_numpy()

    # Get mask information
    if mask_var:
        mc = np.ndarray.flatten(ds[mask_var].to_numpy())
    else:
        mc = np.ones(xc.size)

    # Calculate corner coordinates
    xc_1, yc_1, xo_2, yo_2 = calc_corners(xc, yc)

    # Create new dataset in SCRIP format
    out = xr.Dataset()

    # Fill with data
    out['grid_dims'] = xr.DataArray(np.array(xc.shape[::-1], dtype=np.int32), dims=('grid_rank',))
    out['grid_center_lon'] = xr.DataArray(xc_1, dims=('grid_size'), attrs={'units': 'degrees'})
    out['grid_center_lat'] = xr.DataArray(yc_1, dims=('grid_size'), attrs={'units': 'degrees'})
    out['grid_corner_lon'] = xr.DataArray(xo_2, dims=('grid_size','grid_corners'), attrs={'units': 'degrees'})
    out['grid_corner_lat'] = xr.DataArray(yo_2, dims=('grid_size','grid_corners'), attrs={'units': 'degrees'})
    out['grid_imask'] = xr.DataArray(mc, dims=('grid_size'), attrs={'units': 'unitless'})

    # Force no '_FillValue' if not specified
    for v in out.variables:
        if '_FillValue' not in out[v].encoding:
            out[v].encoding['_FillValue'] = None    

    # Add global attributes
    out.attrs = {'title': 'Grid with {} size'.format('x'.join(list(map(str,xc_1.shape)))),
                 'created_by': os.path.basename(__file__),
                 'date_created': '{}'.format(datetime.now()),
                 'conventions': 'SCRIP'}

    # Write dataset
    if fout is not None:
        out.to_netcdf(fout)

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
    ii = np.ndarray.flatten(np.tile(np.arange(nx), (ny,1)))
    jj = np.ndarray.flatten(np.tile(np.arange(ny), (1,nx)))
    xo_new = np.zeros((xc.size, 4))
    yo_new = np.zeros((yc.size, 4))
    nxp1 = nx+1
    xo_new[:,0] = np.ndarray.flatten(np.ndarray.flatten(xo)[jj*nxp1+ii])
    xo_new[:,1] = np.ndarray.flatten(np.ndarray.flatten(xo)[jj*nxp1+(ii+1)])
    xo_new[:,2] = np.ndarray.flatten(np.ndarray.flatten(xo)[(jj+1)*nxp1+(ii+1)])
    xo_new[:,3] = np.ndarray.flatten(np.ndarray.flatten(xo)[(jj+1)*nxp1+ii])
    yo_new[:,0] = np.ndarray.flatten(np.ndarray.flatten(yo)[jj*nxp1+ii])
    yo_new[:,1] = np.ndarray.flatten(np.ndarray.flatten(yo)[jj*nxp1+(ii+1)])
    yo_new[:,2] = np.ndarray.flatten(np.ndarray.flatten(yo)[(jj+1)*nxp1+(ii+1)])
    yo_new[:,3] = np.ndarray.flatten(np.ndarray.flatten(yo)[(jj+1)*nxp1+ii])    

    # Return flatten arrays
    return(np.ndarray.flatten(xc),
           np.ndarray.flatten(yc),
           xo_new,
           yo_new)
