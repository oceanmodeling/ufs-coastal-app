import os
import sys
import numpy as np
from pyschism.mesh.hgrid import Hgrid
from pyschism.forcing.bctides import Bctides

def execute(opts, start_date, rnday, output_dir="./"):
    # Read horizontal grid
    if os.path.exists(opts["hgrid"]):
        hgrid = Hgrid.open(opts["hgrid"], crs='epsg:4326')
    else:
        print("The file {} does not exist.".format(opts["hgrid"]))
        sys.exit()

    # Define empty lists
    ethconst = []
    vthconst = []
    relax = []    

    # Define indexes
    elev_index = 0
    discharge_index = 0
    relax_index = 0

    for ibnd, flag in enumerate(opts["bctides"]["bctypes"]):
        iettype, ifltype, itetype, isatype = flag

        # Set elevation values
        if iettype == 2:
            ethconst.append(opts["bctides"]["elevation_values"][elev_index] if opts["bctides"]["elevation_values"] else 0.0)
            elev_index += 1
        else:
            ethconst.append(np.nan)

        # Set Discharge values for boundaries
        if ifltype == 2:
            vthconst.append(opts["bctides"]["discharge_values"][discharge_index] if opts["bctides"]["discharge_values"] else 0.0)
            discharge_index += 1
        elif ifltype == -4:
            relax.append(opts["bctides"]["relaxation_inflow"][relax_index] if opts["bctides"]["relaxation_inflow"] else 0.0)
            relax.append(opts["bctides"]["relaxation_outflow"][relax_index] if opts["bctides"]["relaxation_outflow"] else 0.0)
            relax_index += 1
        else:
            vthconst.append(np.nan)

        # 
        if itetype == 2:
            tthconst.append(args.temperature_values[temp_index] if args.temperature_values else 0.0)
            temp_index += 1
            tobc.append(args.temperature_nudging[temp_nudge_index] if args.temperature_nudging else 0.0)
            temp_nudge_index += 1
        elif itetype in [1, 3, 4]:
            tthconst.append(np.nan)
            tobc.append(args.temperature_nudging[temp_nudge_index] if args.temperature_nudging else 0.0)
            temp_nudge_index += 1
        else:
            tthconst.append(np.nan)
            tobc.append(np.nan)


    # Set environment variable
    #if os.path.isdir(opts["bctides"]["tpxo_dir"]):
    #os.environ['TPXO_ELEVATION'] = os.path.join(opts["bctides"]["tpxo_dir"], "h_tpxo9.v1.nc")
    #print(os.environ.get('TPXO_ELEVATION'))
    #else:
    #    print(inspect.getfile(execute))
    #    sys.exit()

    # Call routine that calculates the tidal boundary conditions
    #bctides = Bctides(
    #    hgrid=hgrid,
    #    flags=opts["bctides"]["bctypes"],
    #    constituents=opts["bctides"]["constituents"],
    #    database=opts["bctides"]["database"]
    #    add_earth_tidal=earth_tidal_potential,
    #    cutoff_depth=args.cutoff_depth,
    #    ethconst=ethconst,
    #    vthconst=vthconst,
    #    tthconst=tthconst,
    #    sthconst=sthconst,
    #    tobc=tobc,
    #    sobc=sobc,
    #    relax=relax,
    #)

    # Write tidal boundary conditions to file
    #bctides.write(
    #    output_dir,
    #    start_date=start_date,
    #    rnday=rnday,
    #    overwrite=True,
    #)

    # Return list of files that are generated (used in workflow level)
    return([os.path.join(output_dir, 'bctides.in')])
