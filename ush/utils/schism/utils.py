import numpy as np

def bounding_rectangle_2d(hgrid_fname):
    num_points, num_elements, nodes = read_hgrid(hgrid_fname)
    x_min, y_min = np.min(nodes[:, :2], axis=0)
    x_max, y_max = np.max(nodes[:, :2], axis=0)
    if (x_min < 0):
        x_min = x_min % 360.0
    if (x_max < 0):
        x_max = x_max % 360.0    
    return [x_min, y_min, x_max, y_max]

def read_hgrid(hgrid_fname):
    with open(hgrid_fname, 'r') as file:
        info_string = file.readline().strip()
        num_elements, num_points = map(int, file.readline().split())
        node_coor = np.zeros((num_points, 3))

        for i in range(num_points):
            line = file.readline().split()
            node_id = int(line[0])
            x, y, z = map(float, line[1:])
            node_coor[i] = [x, y, z]

    return num_points, num_elements, node_coor
