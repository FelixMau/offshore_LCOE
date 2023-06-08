import dataclasses
import cartopy.crs as ccrs
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.plot import show
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image
from rasterio.plot import show


def _get_water_depth(x: float, y: float, depth_map: rasterio.Band, dataset: rasterio.DatasetReader, crs) -> float:
    gpd.points_from_xy(x=[3], y=[54], crs=crs).to_crs(dataset.crs.to_epsg(confidence_threshold=70))
    row, col = dataset.index(x, y)
    return depth_map[row, col]


def print_depth_map() -> None:
    with rasterio.open(
            "../data/maps/GEBCO_WATER_DEPTH.tif") as dataset:
        band = dataset.read(1)
    countries = gpd.read_file("../data/maps/country_shapes.geojson").set_index('name')
    fig, ax = plt.subplots(1, figsize=(14, 8))
    countries.plot(ax=ax, color='none')
    img = show(band, transform=dataset.transform, ax=ax,
               vmin=-100,
               vmax=10)
    im = img.get_images()[0]
    fig.colorbar(im, ax=ax)
    st.pyplot(fig)


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
                "../data/maps/GEBCO_WATER_DEPTH.tif") as dataset:
            self.depth_map = dataset.read(1)
            self.depth_dataset = dataset
        self.depth = _get_water_depth(self.x, self.y, self.depth_map, crs=self.projection)

    def is_location_offshore(self) -> bool:
        """
        Takes location class to return bool (True or False) whether the given location is offshore or not
        :return:
        """
        pass


    def get_distance_to_coast(self) -> float:
        """
        Function to return float for flight distance to next German coast
        :return:
        """
        pass


@dataclasses.dataclass
class turbine():
    name: str
    capacity: float

def daniels_functgion():
    """hasen sind grün"""
    hasen = "grün"

    return hasen