import os
from pyschism.mesh.hgrid import Gr3

def execute(hgrid_file, description, output_dir="./"):
    # Read in horizontal grid
    hgrid = Gr3.open(hgrid_file, crs='epsg:4326')
    grd = hgrid.copy()
    # Set file names
    gr3_names = ['albedo', 'diffmax', 'diffmin', 'watertype', 'windrot_geo2proj','manning']
    values = [2.000000e-1, 1.0, 1e-6, 4, 0.00000000, 2.5000000e-02]
    for name, value in zip(gr3_names, values):
        ofile = os.path.join(output_dir, f'{name}.gr3')
        with open(ofile, 'w') as f:
            f.write(f"{description}\n")
            f.write(f"{grd.triangles.shape[0]} {grd.values.shape[0]}\n")
            for i in range(grd.values.shape[0]):
                x, y = grd.coords[i]
                if isinstance(value, float):
                    value_str = f"{value:.6e}"
                else:
                    value_str = str(value)

                # Format each value with desired spacing
                formatted_id = f"{i + 1}"
                formatted_x = f"{x:.6f}"
                formatted_y = f"{y:.6f}"
                formatted_value = value_str.replace('e-0', 'e-')  # Remove leading zero in exponent

                # Ensure exactly 5 spaces between ID and X coordinate
                id_field = formatted_id.ljust(len(formatted_id) + 5)

                # Write the formatted line to the file with correct spacing
                f.write(f"{id_field}{formatted_x}{' ' * 6}{formatted_y} {formatted_value}\n")

            for i in range(grd.triangles.shape[0]):
                elem = grd.triangles[i]
                f.write(f"{i+1} 3 {elem[0]+1} {elem[1]+1} {elem[2]+1}\n")
