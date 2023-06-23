import dataclasses
import cartopy.crs as ccrs
import geopandas as gpd
import pandas as pd
import rasterio
import numpy as np
import shapely
from rasterio.plot import show
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image
from rasterio.plot import show
from collections import namedtuple
import atlite
from sympy import Point, Polygon


def _get_water_depth(
    x: float, y: float, depth_map: rasterio.Band, dataset: rasterio.DatasetReader, crs
) -> namedtuple("water_depth", ["depth_map", "depth"]):

    point = gpd.points_from_xy(x=[float(x)], y=[float(y)], crs=crs).to_crs(
        dataset.crs.to_epsg(confidence_threshold=70)
    )[0]
    row, col = dataset.index(point.x, point.y)

    water_depth = namedtuple("water_depth", ["depth_map", "depth"])
    return water_depth(depth_map=depth_map, depth=depth_map[row, col])


def is_location_offshore(countries=1, point=1) -> bool:
    return not any(countries.geometry.contains(point))


def get_distance_to_coast(
    countries: gpd.GeoDataFrame(), point: shapely.geometry.Point(), toggle: bool = True
) -> float:
    """
    Calculates distance to country shape
    :param countries:
    :param point:
    :param toggle: if True calculates distance to all relevant countries. False only reffers to Germany
    :return: float distance in meters
    """
    germany = countries.loc["DE"]
    denmark = countries.loc["DK"]
    sweden = countries.loc["SE"]
    norway = countries.loc["NO"]

    if toggle == True:
        distance_point = [
            germany.geometry.distance(point),
            denmark.geometry.distance(point),
            sweden.geometry.distance(point),
            norway.geometry.distance(point),
        ]
        min_distance = min(distance_point)
    else:
        min_distance = germany.geometry.distance(point)

    return min_distance


@dataclasses.dataclass
class Location:
    x: float
    y: float
    countries: gpd.GeoDataFrame
    projection: str = "EPSG:4326"
    depth_map: rasterio.Band = dataclasses.field(init=False)
    depth: float = dataclasses.field(init=False)
    ground_material: str = dataclasses.field(init=False)
    point: shapely.geometry.Point = dataclasses.field(init=False)

    def __post_init__(self):
        dataset = rasterio.open("../data/maps/GEBCO_WATER_DEPTH.tif", "r")
        self.depth_map = dataset.read(1)
        self.depth_dataset = dataset
        self.point = gpd.points_from_xy(
            x=[float(self.x)], y=[float(self.y)], crs=self.projection
        ).to_crs(self.depth_dataset.crs.to_epsg(confidence_threshold=70))[0]
        self.depth = _get_water_depth(
            self.x,
            self.y,
            self.depth_map,
            crs=self.projection,
            dataset=self.depth_dataset,
        ).depth


def print_depth_map(location: Location) -> None:
    with rasterio.open("../data/maps/GEBCO_WATER_DEPTH.tif") as dataset:
        band = dataset.read(1)
    countries = gpd.read_file("../data/maps/country_shapes.geojson").set_index("name")
    fig, ax = plt.subplots(1, figsize=(14, 8))
    countries.plot(ax=ax, color="none")
    point = shapely.geometry.Point(location.x, location.y)
    ax.scatter(point.x, point.y, color="red", marker="o", s=50)

    img = show(band, transform=dataset.transform, ax=ax, vmin=-100, vmax=10)
    im = img.get_images()[0]
    fig.colorbar(im, ax=ax)
    st.pyplot(fig)
