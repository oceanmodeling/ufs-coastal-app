from time import time
import os
os.environ['LOCAL_TPXO_DATABASE'] = '/work/noaa/nosofs/mjisan/pyschism-main/PySCHISM_tutorial/data/TPXO'
import argparse
from datetime import datetime, timedelta
import logging
import json

import numpy as np

from pyschism.mesh import Hgrid
from pyschism.forcing.bctides import Bctides

logging.basicConfig(
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    force=True,
)
logging.getLogger("pyschism").setLevel(logging.DEBUG)

def list_of_strings(arg):
    return arg.split(',')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create bctides.in for SCHISM with command-line arguments!")

    # Existing arguments
    parser.add_argument('hgrid', type=str, help='hgrid.ll (lon/lat) file')
    parser.add_argument('start_date', type=datetime.fromisoformat, help='model startdate')
    parser.add_argument('rnday', type=float, help='model rnday')
    parser.add_argument('bctypes', type=str, help="JSON format for Flags for each open boundary, '[[5,5,4,4],[5,5,4,4],[0,1,1,2]]'")
    parser.add_argument('constituents', type=list_of_strings, help="Choose tidal constituents to be included, major, minor, or list of constituents ['K1', 'O1', 'M2']")
    parser.add_argument('database', type=str, help='Tidal database: tpxo or fes2014')

    # New arguments to replace prompts
    parser.add_argument('--earth_tidal_potential', type=str, choices=['Y', 'N'], default='Y', help="Add earth tidal potential? Y/N")
    parser.add_argument('--elevation_values', type=float, nargs='*', help="Elevation values for boundaries with iettype=2")
    parser.add_argument('--discharge_values', type=float, nargs='*', help="Discharge values for boundaries with ifltype=2")
    parser.add_argument('--relaxation_inflow', type=float, nargs='*', help="Relaxation constants for inflow (ifltype=-4)")
    parser.add_argument('--relaxation_outflow', type=float, nargs='*', help="Relaxation constants for outflow (ifltype=-4)")
    parser.add_argument('--temperature_values', type=float, nargs='*', help="Temperature values for boundaries with itetype=2")
    parser.add_argument('--temperature_nudging', type=float, nargs='*', help="Temperature nudging factors")
    parser.add_argument('--salinity_values', type=float, nargs='*', help="Salinity values for boundaries with isatype=2")
    parser.add_argument('--salinity_nudging', type=float, nargs='*', help="Salinity nudging factors")
    parser.add_argument('--cutoff_depth', type=float, default=40.0, help="Cut-off depth for tidal potential")

    args = parser.parse_args()

    try:
        flags = json.loads(args.bctypes)
        print("Parsed bctype list:", flags)
    except json.JSONDecodeError:
        raise TypeError("Invalid JSON format for bctype list.")

    earth_tidal_potential = args.earth_tidal_potential.lower() == 'y'

    ethconst = []
    vthconst = []
    tthconst = []
    sthconst = []
    tobc = []
    sobc = []
    relax = []

    elev_index = 0
    discharge_index = 0
    relax_index = 0
    temp_index = 0
    temp_nudge_index = 0
    salt_index = 0
    salt_nudge_index = 0

    for ibnd, flag in enumerate(flags):
        iettype, ifltype, itetype, isatype = flag

        if iettype == 2:
            ethconst.append(args.elevation_values[elev_index] if args.elevation_values else 0.0)
            elev_index += 1
        else:
            ethconst.append(np.nan)

        if ifltype == 2:
            vthconst.append(args.discharge_values[discharge_index] if args.discharge_values else 0.0)
            discharge_index += 1
        elif ifltype == -4:
            relax.append(args.relaxation_inflow[relax_index] if args.relaxation_inflow else 0.0)
            relax.append(args.relaxation_outflow[relax_index] if args.relaxation_outflow else 0.0)
            relax_index += 1
        else:
            vthconst.append(np.nan)

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

        if isatype == 2:
            sthconst.append(args.salinity_values[salt_index] if args.salinity_values else 0.0)
            salt_index += 1
            sobc.append(args.salinity_nudging[salt_nudge_index] if args.salinity_nudging else 0.0)
            salt_nudge_index += 1
        elif isatype in [1, 3, 4]:
            sthconst.append(np.nan)
            sobc.append(args.salinity_nudging[salt_nudge_index] if args.salinity_nudging else 0.0)
            salt_nudge_index += 1
        else:
            sthconst.append(np.nan)
            sobc.append(np.nan)

    outdir = './'
    hgrid = Hgrid.open(args.hgrid, crs="epsg:4326")

    bctides = Bctides(
        hgrid=hgrid,
        flags=flags,
        constituents=args.constituents,
        database=args.database,
        add_earth_tidal=earth_tidal_potential,
        ethconst=ethconst,
        vthconst=vthconst,
        tthconst=tthconst,
        sthconst=sthconst,
        tobc=tobc,
        sobc=sobc,
        relax=relax,
    )

    bctides = Bctides(
        hgrid=hgrid,
        flags=flags,
        constituents=args.constituents,
        database=args.database,
        add_earth_tidal=earth_tidal_potential,
        cutoff_depth=args.cutoff_depth,
        ethconst=ethconst,
        vthconst=vthconst,
        tthconst=tthconst,
        sthconst=sthconst,
        tobc=tobc,
        sobc=sobc,
        relax=relax,
    )
    bctides.write(
        outdir,
        start_date=args.start_date,
        rnday=args.rnday,
        overwrite=True,
    )

    print(f"Generated bctides.in file in {outdir}")
    print(f"Start date: {args.start_date}")
    print(f"Cutoff depth: {args.cutoff_depth}")
