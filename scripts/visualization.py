from shapely.geometry import Point
from cartopy.crs import PlateCarree as plate
import cartopy.crs as ccrs
import geopandas as gpd
import atlite
import streamlit as st
import topografic
from energyharvest import color_map, Turbine, power_time_series
from topografic import Location
from lcoe import calc_lcoe_from_series
import matplotlib.pyplot as plt
import rasterstats as rs
from collections import namedtuple#

import pydeck as pdk
import pandas as pd
import numpy as np



def chose_windturbine():
    turbine = Turbine(
        name=st.selectbox(
            "Chose Windturbine",
            (
                "NREL_ReferenceTurbine_2016CACost_10MW_offshore",
                "NREL_ReferenceTurbine_2016CACost_6MW_offshore",
                "NREL_ReferenceTurbine_2016CACost_8MW_offshore",
                "NREL_ReferenceTurbine_2019ORCost_12MW_offshore",
                "NREL_ReferenceTurbine_2019ORCost_15MW_offshore",
                "NREL_ReferenceTurbine_2020ATB_12MW_offshore",
                "NREL_ReferenceTurbine_2020ATB_15MW_offshore",
                "NREL_ReferenceTurbine_2020ATB_18MW_offshore",
                "NREL_ReferenceTurbine_5MW_offshore",
                "Vestas_V112_3MW_offshore",
                "Vestas_V164_7MW_offshore",
            ),
        ),
    )
    return turbine


def select_location(countries):
    st.sidebar.title("Coordinates")
    x = st.sidebar.number_input("X coordinate", value=3.0)
    y = st.sidebar.number_input("Y coordinate", value=54.0)
    return Location(x=x, y=y, countries=countries)


def heat_map(turbine: Turbine, cutout: atlite.Cutout, cells: gpd.GeoDataFrame,
             plot_grid_dict: dict, projection, location: Location):
    """
    Calculates lcoe for every cell with windspeed data and returns GeoDataFrame.
    :param turbine: Turbine clas
    :param cutout: cutout with wind data for one year (different timeframes would change lcoe)
    :param cells: GeoDataframe with raster shapes for
    :param plot_grid_dict:
    :param projection:
    :param location:
    :return:
    """
    config = namedtuple("conffig", ["year", "turbine", "other_countries"])
    cap_factors = (
        cutout.wind(turbine=turbine.name, capacity_factor=False) * turbine.capacity
    )
    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))

    cap_factors = gpd.GeoDataFrame(
        cap_factors.to_dataframe(),
        geometry=gpd.points_from_xy(
            cap_factors.to_dataframe().lon, cap_factors.to_dataframe().lat
        ),
    )

    stats = rs.zonal_stats(
        cells.geometry,
        location.depth_dataset.read(1),
        affine=location.depth_dataset.transform,
        stats=["mean"],
    )
    toggle = st.checkbox("Allow connection to other countries", value=True)

    cap_factors.reset_index()
    cap_factors["depth"] = [x["mean"] for x in stats]
    cap_factors["lcoe"] = cap_factors.apply(
        calc_lcoe_from_series, axis=1, **{"capacity": turbine.capacity,
                                          "countries": location.countries,
                                          "toggle": toggle}
    )

    cap_factors.name = "Capacity Factor"
    cap_factors.plot(
        column="lcoe", ax=ax, transform=plate(), legend=True, vmin=20, vmax=40
    )
    cells.plot(ax=ax, **plot_grid_dict)
    fig.tight_layout()

    # Display the plot in the main section
    st.pyplot(fig)
    return cap_factors


def pydeck(heat):
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    view = pdk.data_utils.compute_view(heat[["lon", "lat"]])
    view.pitch = 75
    view.bearing = 60
    #heat.drop(["lon", "lat", "specific generation", "depth"], axis=1, inplace=True)

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=view,
        layers=[
        pdk.Layer(
           'ColumnLayer',
           data=heat,
           get_position="geometry.coordinates",
           get_elevation="specific generation",
           elevation_scale = 1,
           radius=1000,
           pickable=True,
           auto_highlight=True,
        ),
    ],
    ))
    pass


def main():
    # # Reading cutout for given year:
    #
    cutout = atlite.Cutout("../data/weather/western-europe-2011.nc")
    cutout.prepare()
    #
    url = "https://tubcloud.tu-berlin.de/s/7bpHrAkjMT3ADSr/download/country_shapes.geojson"
    countries = gpd.read_file(url).set_index("name")
    projection = ccrs.PlateCarree()
    #
    plot_grid_dict = dict(
        alpha=0.1,
        edgecolor="k",
        zorder=4,
        aspect="equal",
        facecolor="None",
        transform=plate(),
    )
    #
    # # Add a title to your app
    st.title("Wind Data Visualization")
    #
    turbine = chose_windturbine()
    #
    cells = cutout.grid
    #
    color_map(turbine.name, cutout, cells, plot_grid_dict, projection)
    #
    location = select_location(countries=countries)
    #
    power_yield = power_time_series(cutout, turbine, location=location)
    #
    topografic.print_depth_map(location)
    #
    heat = heat_map(turbine, cutout, cells, plot_grid_dict, projection, location)
    #pydeck(heat)


if __name__ == "__main__":
    main()
