"""
SCHISM Boundary Condition Generator for UFS-Coastal App (gen_bctides.py)
------------------------------------------------------------------------

Features:
- Generates boundary condition files (bctides.in, elev2D.th.nc) for SCHISM
- Supports:
  * Tidal (type 3)
  * Time-elevation (type 4) from elev.th or HYCOM data
  * Temperature and salinity from HYCOM
- Auto-detects open boundaries from hgrid.ll

Usage:
1. Tidal boundary (type 3):
   python gen_bctides.py hgrid.ll 2024-01-01 10 \
       --bc_mode tidal \
       --bc_type 3 \
       --constituents K1,O1,M2,S2,N2,P1,Q1 \
       --database tpxo \
       --earth_tidal_potential Y

2. Time-elevation from file (type 4):
   python gen_bctides.py hgrid.ll 2024-01-01 10 \
       --bc_mode time-elev \
       --bc_type 4 \
       --elev_source timeseries \
       --elev_th elev.th \
       --vgrid vgrid.in

3. HYCOM boundary conditions:
   python gen_bctides.py hgrid.ll 2024-01-01 10 \
       --bc_mode time-elev \
       --bc_type 4 \
       --elev_source hycom \
       --gen_bc elev,temp,salt \
       --vgrid vgrid.in

Required files:
- hgrid.ll: SCHISM horizontal grid file
- vgrid.in: Vertical grid file (for time-elev mode)
- elev.th: Time series file (if using timeseries source)

Example Use Cases:
a. Ike Shinnecock with tidal boundaries:
   python gen_bctides.py hgrid.ll 2008-08-23 20 \
       --bc_mode tidal \
       --bc_type 3 \
       --constituents Q1,O1,P1,K1,N2,M2,S2,K2,Mm,Mf,M4,MN4,MS4,2N2,S1 \
       --database tpxo \
       --cutoff_depth 40 \
       --earth_tidal_potential Y

b. Duck, NC with time series:
   python gen_bctides.py hgrid.ll 2012-10-27 2.333 \
       --bc_mode time-elev \
       --bc_type 4 \
       --elev_source timeseries \
       --elev_th elev.th \
       --vgrid vgrid.in

Contact:

Mansur Ali Jisan (mansur.jisan@noaa.gov)
NOAA/NOS/CO-OPS

Version: 1.1
Last Updated: January 2025
"""

import os
import numpy as np
import logging
from netCDF4 import Dataset
from pyschism.mesh.vgrid import Vgrid
from pyschism.mesh import Hgrid
from pyschism.forcing.bctides import Bctides
from pyschism.forcing.hycom.hycom2schism import OpenBoundaryInventory

def create_boundary_flags(num_nodes, bc_type, additional_flags=None):
    """
    Create boundary flags automatically using node count from hgrid.ll
    Args:
        num_nodes: list of node counts from hgrid.ll
        bc_type: boundary condition type (e.g., 3 for tidal, 4 for timeseries of water elevation)
        additional_flags: additional flag values
    Returns:
        List of boundary flags
    """

    # For tidal boundaries (type 3)
    if bc_type == 3:
        flags = []
        for _ in num_nodes:  
            flags.append([3, 0, 0, 0])  
        return flags
    
    # For other boundary types (type 4)
    if additional_flags is None:
        additional_flags = [0, 0, 0]
    
    flags = []
    for nodes in num_nodes:
        flags.append([nodes, bc_type] + additional_flags)
    
    return flags

def create_elev2d_th_nc(filename, timeseries_data, hgrid, vgrid):
    open_boundaries = hgrid.boundaries.open
    nOpenBndNodes = sum(len(boundary) for boundary in open_boundaries['indexes'])
    time_data = timeseries_data[:, 0]
    elev_data = timeseries_data[:, 1]
    
    with Dataset(filename, 'w', format='NETCDF4') as nc:

        # Define dimensions
        nc.createDimension('nComponents', 1)
        nc.createDimension('nLevels', 1)
        nc.createDimension('time', None)
        nc.createDimension('nOpenBndNodes', nOpenBndNodes)
        nc.createDimension('one', 1)
        
        # Create variables
        nComponents = nc.createVariable('nComponents', 'f8', ('nComponents',))
        nComponents.point_spacing = "even"
        nComponents.axis = "X"
        
        nLevels = nc.createVariable('nLevels', 'f8', ('nLevels',))
        nLevels.point_spacing = "even"
        nLevels.axis = "Y"
        
        time = nc.createVariable('time', 'f8', ('time',))
        time[:] = time_data
        
        time_series = nc.createVariable('time_series', 'f4', 
                                      ('time', 'nOpenBndNodes', 'nLevels', 'nComponents'))
        for t in range(len(time_data)):
            time_series[t, :, 0, 0] = elev_data[t]
            
        time_step = nc.createVariable('time_step', 'f4', ('one',))
        time_step[:] = time_data[1] - time_data[0]
        
        nc.Conventions = "CF-1.6"
        nc.history = "Created by SCHISM boundary condition generator"

def create_elev2d_from_hycom(hgrid, vgrid, outdir, start_date, rnday, ocean_bnd_ids=None, elev2D=True, TS=False, UV=False, hgrid_file=None):
    if ocean_bnd_ids is None:
        num_boundaries, _ = read_hgrid_boundaries(hgrid_file)
        ocean_bnd_ids = list(range(num_boundaries))
    
    # Convert vgrid object to path string if needed
    vgrid_path = vgrid.path if hasattr(vgrid, 'path') else args.vgrid
    
    try:
        logging.info("elev2D = %s, TS = %s, UV = %s", elev2D, TS, UV)
        logging.info("Ocean boundaries: %s", ' '.join(map(str, ocean_bnd_ids)))
        bnd = OpenBoundaryInventory(hgrid, vgrid_path)
        bnd.fetch_data(outdir, start_date, rnday, elev2D=elev2D, TS=TS, UV=UV,
                      ocean_bnd_ids=ocean_bnd_ids)
    except Exception as e:
        logging.error("Error details: hgrid type is %s and vgrid type is %s", type(hgrid), type(vgrid))
        raise e
    
def read_hgrid_boundaries(hgrid_file):
    """
    Read boundary information from hgrid.ll file
    Supports multiple formats:
    1. '= Number of open boundaries'
    2. '! total number of ocean boundaries'
    
    Returns:
        - Number of open boundaries
        - List of number of nodes for each boundary
    """
    if not os.path.exists(hgrid_file):
        raise FileNotFoundError(f"hgrid.ll file not found: {hgrid_file}")
        
    with open(hgrid_file, 'r') as f:
        lines = f.readlines()
    
    try:    
        # Search for the statement 'number of open boundaries' / 'total number of ocean boundaries' in hgrid.ll file. Try both formats
        for i, line in enumerate(lines):
            # Format 1: "= Number of open boundaries"
            if '= Number of open boundaries' in line:
                num_open_boundaries = int(line.split('=')[0].strip())
                total_nodes = int(lines[i+1].split('=')[0].strip())
                nodes_per_boundary = []
                current_line = i + 2
                
                for _ in range(num_open_boundaries):
                    num_nodes = int(lines[current_line].split('=')[0].strip())
                    nodes_per_boundary.append(num_nodes)
                    current_line += 1
                    
                return num_open_boundaries, nodes_per_boundary
                
            # Format 2: "! total number of ocean boundaries"
            elif '! total number of ocean boundaries' in line:
                num_open_boundaries = int(line.split('!')[0].strip())
                total_nodes = int(lines[i+1].split('!')[0].strip())
                nodes_per_boundary = []
                current_line = i + 2
                
                for _ in range(num_open_boundaries):
                    num_nodes = int(lines[current_line].split('!')[0].strip())
                    nodes_per_boundary.append(num_nodes)
                    current_line += 1
                    
                return num_open_boundaries, nodes_per_boundary
        
        # If neither format is found
        logging.info("Warning: Attempting alternative format search...")
        
        # Try looking for any line containing boundary information
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['boundary', 'boundaries', 'open', 'ocean']):
                try:
                    # Try to extract the first number from the line
                    nums = [int(s) for s in line.split() if s.isdigit()]
                    if nums:
                        num_open_boundaries = nums[0]
                        total_nodes = int(lines[i+1].split()[0])
                        nodes_per_boundary = []
                        current_line = i + 2
                        
                        for _ in range(num_open_boundaries):
                            num_nodes = int(lines[current_line].split()[0])
                            nodes_per_boundary.append(num_nodes)
                            current_line += 1
                            
                        logging.info("Found boundary information using alternative format")
                        return num_open_boundaries, nodes_per_boundary
                except:
                    continue
                    
        raise ValueError("Could not find boundary information in any recognized format")
        
    except (IndexError, ValueError) as e:
        logging.error("Failed to parse hgrid.ll file at line %s", current_line if 'current_line' in locals() else 'unknown')
        logging.error("Problematic line content: %s", lines[current_line] if 'current_line' in locals() else 'unknown')
        raise ValueError(f"Error parsing hgrid.ll file: {str(e)}")

def write_timelev_bctides(outdir, start_date, flags):
    """Write timeseries of water elevation bctides.in file for type 4 boundary conditions"""
    with open(f"{outdir}/bctides.in", 'w') as f:
        f.write(f"{start_date.strftime('%m/%d/%Y %H:%M:%S')} UTC\n")
        f.write(" 0  0.000   ! number of earth tidal potential, cut-off depth\n")
        f.write(" 0          ! number of boundary forcing freqs\n")
        f.write(f" {len(flags)}          ! number of open boundaries\n")
        for flag in flags:
            f.write(f" {' '.join(map(str, flag))} ! type of b.c.\n")

def execute(opts, start_date, rnday, output_dir="./"):
    # Check grid files
    if os.path.exists(opts["hgrid"]):
        hgrid = opts["hgrid"]
    else:
        logging.error("The file %s does not exist.", opts["hgrid"])
        sys.exit()
    if os.path.exists(opts["vgrid"]):
        vgrid = opts["vgrid"]
    else:
        logging.error("The file %s does not exist.", opts["vgrid"])
        sys.exit()
  
    # Check arguments
    if "bctides" in opts.keys():
        # Boundary condition mode
        bc_mode = "tidal"
        if "mode" in opts["bctides"].keys():
            bc_mode = opts["bctides"]["mode"]

        # Tidal mode arguments
        constituents = []
        if "constituents" in opts["bctides"].keys():
            constituents = opts["bctides"]["constituents"]
        database = "tpxo"
        if "database" in opts["bctides"].keys():
            database = opts["bctides"]["database"]
        if database == "tpxo":
            if "tpxo_dir" in opts["bctides"].keys():
                os.environ["TPXO_ELEVATION"] = os.path.join(opts["bctides"]["tpxo_dir"], "h_tpxo9.v1.nc")
                os.environ["TPXO_VELOCITY"] = os.path.join(opts["bctides"]["tpxo_dir"], "u_tpxo9.v1.nc")
        earth_tidal_potential = 'Y'
        if "earth_tidal_potential" in opts["bctides"].keys():
            earth_tidal_potential = 'Y' if opts["bctides"]["earth_tidal_potential"] else 'N'
        cutoff_depth = 40.0
        if "cutoff_depth" in opts["bctides"].keys():
            cutoff_depth = opts["bctides"]["cutoff_depth"]

        # Additional boundary parameters
        if "elevation_values" in opts["bctides"].keys():
            elevation_values = opts["bctides"]["elevation_values"]
        if "discharge_values" in opts["bctides"].keys():
            discharge_values = opts["bctides"]["discharge_values"]
        if "relaxation_inflow" in opts["bctides"].keys():
            relaxation_inflow = opts["bctides"]["relaxation_inflow"]
        if "relaxation_outflow" in opts["bctides"].keys():
            relaxation_outflow = opts["bctides"]["relaxation_outflow"]
        if "temperature_values" in opts["bctides"].keys():
            temperature_values = opts["bctides"]["temperature_values"]
        if "temperature_nudging" in opts["bctides"].keys():
            temperature_nudging = opts["bctides"]["temperature_nudging"]
        if "salinity_values" in opts["bctides"].keys():
            salinity_values = opts["bctides"]["salinity_values"]
        if "salinity_nudging" in opts["bctides"].keys():
            salinity_nudging = opts["bctides"]["salinity_nudging"]
        if "bc_type" in opts["bctides"].keys():
            bc_type = opts["bctides"]["bc_type"]
        if "elev_th" in opts["bctides"].keys():
            elev_th = opts["bctides"]["elev_th"]
        additional_flags = [] 
        if "additional_flags" in opts["bctides"].keys():
            additional_flags = opts["bctides"]["additional_flags"]
        if "elev_source" in opts["bctides"].keys():
            elev_source = opts["bctides"]["elev_source"]
        if "ocean_bnd_ids" in opts.keys():
            ocean_bnd_ids = opts["ocean_bnd_ids"]
        if "gen_bc" in opts["bctides"].keys():
            gen_bc = opts["gen_bc"]
        else:
            gen_bc = "elev"

    # Generate files 
    try:
        num_boundaries, nodes_per_boundary = read_hgrid_boundaries(hgrid)
        flags = create_boundary_flags(nodes_per_boundary, bc_type, additional_flags)
        
        if bc_mode == 'time-elev':
            hgrid = Hgrid.open(hgrid, crs="epsg:4326")
            vgrid = Vgrid.open(vgrid) if vgrid else None
            
            # Generate bctides.in
            write_timelev_bctides(output_dir, start_date, flags)
            
            # Generate elev2D.th.nc based on source
            if elev_source == 'timeseries':
                if not elev_th:
                    raise ValueError("Elevation timeseries file (--elev_th) required for timeseries mode")
                timeseries_data = np.loadtxt(elev_th)
                create_elev2d_th_nc('elev2D.th.nc', timeseries_data, hgrid, vgrid)
            elif elev_source == 'hycom':
                # Convert options to booleans
                elev2D = 'elev' in gen_bc
                TS = any(x in gen_bc for x in ['temp', 'salt'])
                UV = 'vel' in gen_bc
    
                ocean_bnd_ids = [int(i) for i in ocean_bnd_ids] if ocean_bnd_ids else None

                create_elev2d_from_hycom(hgrid, vgrid, output_dir, start_date, rnday,
                                         ocean_bnd_ids=ocean_bnd_ids, elev2D=elev2D, TS=TS, UV=UV,
                                         hgrid_file=hgrid)
                

            logging.info("Successfully generated boundary files:")
            logging.info("  bctides.in  : %s", output_dir)
            logging.info("  elev2D.th.nc: %s", os.path.abspath('elev2D.th.nc'))
            logging.info("  Start date  : %s", start_date)
        else:
            # Verify required tidal arguments
            if not constituents or not database:
                raise ValueError("Constituents and database are required for tidal mode")

            earth_tidal_potential = earth_tidal_potential.lower() == 'y'

            # Initialize boundary condition arrays
            ethconst = []
            vthconst = []
            tthconst = []
            sthconst = []
            tobc = []
            sobc = []
            relax = []

            # Process boundary conditions
            elev_index = discharge_index = relax_index = temp_index = 0
            temp_nudge_index = salt_index = salt_nudge_index = 0

            for ibnd, flag in enumerate(flags):
                iettype, ifltype, itetype, isatype = flag

                # Process elevation
                if iettype == 2:
                    ethconst.append(elevation_values[elev_index] if elevation_values else 0.0)
                    elev_index += 1
                else:
                    ethconst.append(np.nan)

                # Process flow
                if ifltype == 2:
                    vthconst.append(discharge_values[discharge_index] if discharge_values else 0.0)
                    discharge_index += 1
                elif ifltype == -4:
                    relax.append(relaxation_inflow[relax_index] if relaxation_inflow else 0.0)
                    relax.append(relaxation_outflow[relax_index] if relaxation_outflow else 0.0)
                    relax_index += 1
                else:
                    vthconst.append(np.nan)

                # Process temperature
                if itetype == 2:
                    tthconst.append(temperature_values[temp_index] if temperature_values else 0.0)
                    temp_index += 1
                    tobc.append(temperature_nudging[temp_nudge_index] if temperature_nudging else 0.0)
                    temp_nudge_index += 1
                elif itetype in [1, 3, 4]:
                    tthconst.append(np.nan)
                    tobc.append(temperature_nudging[temp_nudge_index] if temperature_nudging else 0.0)
                    temp_nudge_index += 1
                else:
                    tthconst.append(np.nan)
                    tobc.append(np.nan)

                # Process salinity
                if isatype == 2:
                    sthconst.append(salinity_values[salt_index] if salinity_values else 0.0)
                    salt_index += 1
                    sobc.append(salinity_nudging[salt_nudge_index] if salinity_nudging else 0.0)
                    salt_nudge_index += 1
                elif isatype in [1, 3, 4]:
                    sthconst.append(np.nan)
                    sobc.append(salinity_nudging[salt_nudge_index] if salinity_nudging else 0.0)
                    salt_nudge_index += 1
                else:
                    sthconst.append(np.nan)
                    sobc.append(np.nan)

            hgrid = Hgrid.open(hgrid, crs="epsg:4326")

            bctides = Bctides(
                hgrid=hgrid,
                flags=flags,
                constituents=constituents,
                database=database,
                add_earth_tidal=earth_tidal_potential,
                cutoff_depth=cutoff_depth,
                ethconst=ethconst,
                vthconst=vthconst,
                tthconst=tthconst,
                sthconst=sthconst,
                tobc=tobc,
                sobc=sobc,
                relax=relax,
            )
            
            bctides.write(
                output_dir,
                start_date=start_date,
                rnday=rnday,
                overwrite=True,
            )

            # Return list of files that are generated (used in workflow level)
            return([os.path.join(output_dir, 'bctides.in')])

    except Exception as e:
        logging.error(str(e))
        sys.exit()
