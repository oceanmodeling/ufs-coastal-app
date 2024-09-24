import os
import sys
from uwtools.logging import log
from pyschism.mesh.hgrid import Hgrid
from pyschism.forcing.hycom.hycom2schism import OpenBoundaryInventory

def execute(hgrid_file, vgrid_file, start_date, rnday, ocean_bnd_ids, output_dir="./", elev=True, ts=True, uv=True):
    '''
    outputs:
        elev2D.th.nc (elev=True)
        SAL_3D.th.nc (TS=True)
        TEM_3D.th.nc (TS=True)
        uv3D.th.nc   (UV=True)
    '''
    # read horizontal grid
    if os.path.exists(hgrid_file):
        hgrid = Hgrid.open(hgrid_file, crs='epsg:4326')
    else:
        print("The file {} does not exist.".format(hgrid_file))
        sys.exit()
    # create open boundary object
    if os.path.exists(vgrid_file):
        bnd = OpenBoundaryInventory(hgrid, vgrid_file)
    else:
        print("The file {} does not exist.".format(vgrid_file))
        sys.exit()
    # create open boundary data files
    # ocean_bnd_ids - segment indices, starting from zero
    bnd.fetch_data(output_dir, start_date, rnday, elev2D=elev, TS=ts, UV=uv, ocean_bnd_ids=ocean_bnd_ids)
