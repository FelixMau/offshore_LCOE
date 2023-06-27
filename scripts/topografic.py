import dataclasses
import geopandas as gpd
import rasterio
import shapely
import matplotlib.pyplot as plt
import streamlit as st
from rasterio.plot import show
from collections import namedtuple
from pyproj import CRS


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

    gdf_utm = countries.to_crs(CRS.from_epsg(32633))  # UTM zone 33N, change the EPSG code as needed
    point_utm = gpd.GeoSeries(point).set_crs(CRS.from_epsg(4326)).to_crs(CRS.from_epsg(32633)).iloc[0]

    germany = gdf_utm.loc["DE"]
    denmark = gdf_utm.loc["DK"]
    sweden = gdf_utm.loc["SE"]
    norway = gdf_utm.loc["NO"]

    if toggle == True:
        distance_point = [
            germany.geometry.distance(point_utm),
            denmark.geometry.distance(point_utm),
            sweden.geometry.distance(point_utm),
            norway.geometry.distance(point_utm),
        ]
        min_distance = min(distance_point)
    else:
        min_distance = germany.geometry.distance(point_utm)

    return min_distance/1000


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
