import dataclasses
import cartopy.crs as ccrs
import geopandas as gpd
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


def _get_water_depth(
    x: float, y: float, depth_map: rasterio.Band, dataset: rasterio.DatasetReader, crs
) -> namedtuple("water_depth", ["depth_map", "depth"]):

    point = gpd.points_from_xy(x=[float(x)], y=[float(y)], crs=crs).to_crs(
        dataset.crs.to_epsg(confidence_threshold=70)
    )[0]
    row, col = dataset.index(point.x, point.y)

    water_depth = namedtuple("water_depth", ["depth_map", "depth"])
    return water_depth(depth_map=depth_map, depth=depth_map[row, col])


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
        ).depth_map

    def is_location_offshore(self) -> bool:
        """
        Takes location class to return bool (True or False) whether the given location is offshore or not
        -> Google: "Check if point is in geopandas shape" oder so ähnlich.
            Den Geopandas dataframe (also countries bekommt man durch: self.countries
            Den Point durch self.point (es ist ein geopandas point)
        :return:
        """
        pass

    def get_distance_to_coast(self) -> float:
        """
        Function to return float for flight distance to next German coast
        Google: "get distance point to shape"
            geopandas shapes (also countries findet ihr in self.countries)
            den point wieder in self.point
            Eventuell muss der Geopandas dataframe auf "DE" reduziert werden.
                Am anpassungsfähigsten ist die funktion dann wenn wir einen trigger einbauen der kann ja auch default
                auf True gesetzt werden mit dem man nur den Abstand zu Deutschladn oder eben auch zu den anderen
                Ländern setzen kann. Um Defaults zu setzen würde die Methodendefinition sich zu
                def get_distance_to_coast(self, only_germany:bool = True) -> float: ändern
                Später kann dann so (wenn wir das dann wollen) diese Funktion über einen Knopf in der App angeschaltet
                werden



            Kleine Nachhilfe in annotations:
                Sinn von annotations: Eine gute IDE (wie Pycharm) checkt ob man alles richtig macht und
                ob die richtigen Variabletypen übergeben werden wenn alles annotiert ist vereinfacht dass
                das coding und die Wartung des Codes.
                -> float : gibt an was die Funktion zurückgeben soll
                :bool gibt an dass die eingangssvariable eine bool variable ist also entweder True oder False

            
        :return:
        """
        return self.x




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
