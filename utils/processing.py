import PIL
import numpy as np
import cv2

from PIL import Image
PIL.Image.MAX_IMAGE_PIXELS = None


class Satellite_Map:
  def __init__(self, origin, values, shape, coord):
    self.origin = origin
    self.shape = (shape[0], shape[1])
    self.coord = coord
    self.values = values


class Coord:
    def __init__(self, lat_min, lat_max, lon_min, lon_max):
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.lat_min = lat_min
        self.lat_max = lat_max

    def show(self):
        print(self.lat_min, self.lat_max, self.lon_min, self.lon_max)


class Index:
    def __init__(self, row_min, row_max, col_min, col_max):
        self.col_min = col_min
        self.col_max = col_max
        self.row_min = row_min
        self.row_max = row_max

    def show(self):
        print(self.row_min, self.row_max, self.col_min, self.col_max)


def convert_deg_to_ha(area_deg: float):
    """
    converts  value in degrees^2
    (of latitude and longitude)
    into a value in hectars ha

    #Parameters:
    #    area_deg (float): The value in deg^2 to be converted

    #Returns:
    #    converted value in ha
    """
    scale_m_per_deg = 30 / 0.00025
    return area_deg * (scale_m_per_deg ** 2) / 10000  # ha


def calculate_deg_per_pixel(map_shape, coord):
    """
    returns the length in degrees per pixel ratio for the drone imagery
    """
    # degrees per pixel
    lon_res = (coord.lon_max - coord.lon_min) / map_shape[1]
    lat_res = (coord.lat_max - coord.lat_min) / map_shape[0]

    if lat_res > lon_res:
        return lat_res
    else :
        return lon_res



def raster_to_image(raster):
    """
    Parameters:
    raster object with at least three channels 1:Red, 2:Green, 3: Blue

    Return:
    a 3byX numpy array for the RGB values of the drone image

    """
    red = raster.read(1)
    green = raster.read(2)
    blue = raster.read(3)

    image = np.dstack((red, green, blue))

    # Filtering out the white pixels and scaling to true value
    white = red
    white = np.where((red == 255) & (blue == 255) & (green == 255), 0, 1)

    return image, white



def get_bounds(field_data, site_no):
    lat_min = field_data.iloc[site_no]['lat_min']
    lat_max = field_data.iloc[site_no]['lat_max']
    lon_min = field_data.iloc[site_no]['lon_min']
    lon_max = field_data.iloc[site_no]['lon_max']

    return Coord(lat_min, lat_max, lon_min, lon_max)


# Convert lat and lon into row and col
def convert_geocoord_to_row_and_col(raster, coord):
    row_min, col_min = raster.index(coord.lon_min, coord.lat_max)
    row_max, col_max = raster.index(coord.lon_max, coord.lat_min)

    return Index(row_min, row_max, col_min, col_max)


def get_new_bounds(coord, pixel_ratio, index):
    lat_min_new = coord.lat_max - (pixel_ratio * index.row_max)
    lat_max_new = coord.lat_max - (pixel_ratio * index.row_min)

    lon_min_new = coord.lon_min + (pixel_ratio * index.col_min)
    lon_max_new = coord.lon_min + (pixel_ratio * index.col_max)

    return Coord(lat_min_new, lat_max_new, lon_min_new, lon_max_new)


# Cropping the AGB data to fit the plot
def crop_map_to_site(raster, map_values, drone_raster, drone_image, field_data, site_no):

    # crop map to low-res size
    field_coord = get_bounds(field_data, site_no)
    raster_coord = Coord(raster.bounds[1], raster.bounds[3], raster.bounds[0], raster.bounds[2])

    pixel_ratio_pre = calculate_deg_per_pixel(raster.shape, raster_coord)

    init_index = convert_geocoord_to_row_and_col(raster, field_coord)
    init_index = add_index_padding(raster_coord, pixel_ratio_pre, init_index)

    # select which bands that have correct values
    map_crude = map_values[init_index.row_min:init_index.row_max, init_index.col_min:init_index.col_max]

    # resize image to high-res size
    new_coords = get_new_bounds(raster_coord, pixel_ratio_pre, init_index)

    pixel_ratio_drone = calculate_deg_per_pixel(drone_raster.shape, field_coord)

    new_shape = new_resize_shape(pixel_ratio_drone, new_coords, drone_image.shape)

    map_resized = resize_map(map_crude, new_shape)

    # crop new resized map to perfectly fit the site coordinates
    new_index = get_index_by_coordinates(pixel_ratio_drone, field_coord, new_coords, drone_raster.shape, map_resized)

    map_fitted = map_resized[new_index.row_min:new_index.row_max, new_index.col_min:new_index.col_max]
    # np.save("../../data/GFW_site_().npy".format(site_no), map_filtered)

    return map_crude, map_resized, map_fitted


def new_resize_shape(pixel_ratio_ideal, coord, ideal_shape):
    lon_diff = coord.lon_max - coord.lon_min
    lat_diff = coord.lat_max - coord.lat_min

    shape = [int(lat_diff / pixel_ratio_ideal), int(lon_diff / pixel_ratio_ideal)]

    if shape[0] < ideal_shape[0]:
        shape[0] = ideal_shape[0]
    if shape[1] < ideal_shape[1]:
        shape[1] = ideal_shape[1]

    return shape


# Resize the cropped image to have the same pixel resolution as the HR image
def resize_map(map_values, new_shape):
    map_resized = cv2.resize(map_values,
                             dsize=((new_shape[1], new_shape[0])),
                             interpolation=cv2.INTER_LINEAR)

    return map_resized



# Crop the already cropped image by the bounds of the HR image
def get_index_by_coordinates(pixel_ratio, coord_old, coord_new, ideal_shape, map_tbd):

    row_min = int((coord_new.lat_max - coord_old.lat_max) / pixel_ratio)
    row_max = row_min + (ideal_shape[0])

    col_min = int((coord_old.lon_min - coord_new.lon_min) / pixel_ratio)
    col_max = col_min + (ideal_shape[1])

    # in case it goes beyond the borders for one dimension, it needs to be reshifted
    if map_tbd.shape[0] < row_max:
        row_max = map_tbd.shape[0]
        row_min = map_tbd.shape[0] - ideal_shape[0]

    if map_tbd.shape[1] < col_max:
        col_max = map_tbd.shape[1]
        col_min = map_tbd.shape[1] - ideal_shape[1]

    return Index(row_min, row_max, col_min, col_max)


def add_index_padding(coord, pixel_ratio, index):
    new_coord = get_new_bounds(coord, pixel_ratio, index)

    # check if the boundaries are large enough
    if new_coord.lat_max < coord.lat_max:
        index.row_min -= 1
    if new_coord.lat_min > coord.lat_min:
        index.row_max += 1
    if new_coord.lon_min > coord.lon_min:
        index.col_min -= 1
    if new_coord.lon_max < coord.lon_max:
        index.col_max += 1

    return index
