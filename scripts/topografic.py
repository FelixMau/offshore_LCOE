import dataclasses
import cartopy.crs as ccrs
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.plot import show
import matplotlib.pyplot as plt

from rasterio.plot import show


def get_water_depth(x: float, y: float, depth_map: rasterio.Band, dataset: rasterio.DatasetReader, crs) -> float:
    gpd.points_from_xy(x=[3], y=[54], crs=crs).to_crs(dataset.crs.to_epsg(confidence_threshold=70))
    row, col = dataset.index(x, y)
    return depth_map[row, col]


def print_depth_map() -> plt.axes:
    with rasterio.open(
            "/home/felix/PycharmProjects/offshore_LCOE/data/GEBCO_29_May_2023_2c33d4d8c3a0/gebco_2023_n57.0_s52.0_w3.0_e18.0.tif") as dataset:
        band = dataset.read(1)
        return show(band)


@dataclasses.dataclass
class location():
    x: float
    y: float
    countries: gpd.GeoDataFrame
    projection: str = "EPSG:4326"
    depth_map: rasterio.Band = dataclasses.field(init=False)
    depth: float = dataclasses.field(init=False)
    ground_material: str = dataclasses.field(init=False)


    def __post_init__(self):
        with rasterio.open(
                "/home/felix/PycharmProjects/offshore_LCOE/data/GEBCO_29_May_2023_2c33d4d8c3a0/gebco_2023_n57.0_s52.0_w3.0_e18.0.tif") as dataset:
            self.depth_map = dataset.read(1)
            self.depth_dataset = dataset
        self.depth = get_water_depth(self.x, self.y, self.depth_map, crs=self.projection)

    def is_location_at_sea(self):
        pass


@dataclasses.dataclass
class turbine():
    name: str
    capacity: float
