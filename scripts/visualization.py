from shapely.geometry import Point
from cartopy.crs import PlateCarree as plate
import cartopy.crs as ccrs
import geopandas as gpd
import atlite
import streamlit as st
import topografic
from energyharvest import color_map, Turbine, power_time_series, duration_curve
from topografic import Location, get_distance_to_coast
from lcoe import calc_lcoe_from_series, calc_lcoe
import matplotlib.pyplot as plt
import rasterstats as rs
from collections import namedtuple  #

import pydeck as pdk
import pandas as pd
import numpy as np


def select_location_and_turbine(countries):
    st.sidebar.title("Settings")
    x = st.sidebar.number_input("X coordinate", value=3.0)
    y = st.sidebar.number_input("Y coordinate", value=54.0)
    turbine = Turbine(
        name=st.sidebar.selectbox(
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
    upper_lower = st.sidebar.selectbox("Upper, lower values?", ("upper", "lower"))
    other_countries_connection = st.sidebar.checkbox(
        "Allow connection to other countries", value=True
    )
    return (
        Location(x=x, y=y, countries=countries),
        turbine,
        upper_lower,
        other_countries_connection,
    )


def heat_map(
    turbine: Turbine,
    cap_factors,
    cells: gpd.GeoDataFrame,
    plot_grid_dict: dict,
    projection,
    location: Location,
    other_countries_connection,
    value,
):
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

    cap_factors.reset_index()
    cap_factors["depth"] = [x["mean"] for x in stats]
    cap_factors["lcoe"] = cap_factors.apply(
        calc_lcoe_from_series,
        axis=1,
        **{
            "capacity": turbine.capacity,
            "countries": location.countries,
            "other_countries_connection": other_countries_connection,
            "value": value,
        },
    )
    cap_factors.rename(columns={"lcoe": "lcoe [€/MWh]"}, inplace=True)  #
    limit = cap_factors.sort_values(by="lcoe [€/MWh]", ascending=False).iloc[10]["lcoe [€/MWh]"]
    cap_factors = cap_factors.to_xarray()["lcoe [€/MWh]"]

    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))
    cap_factors.plot(ax=ax, transform=plate(), vmax=limit)

    cells.plot(ax=ax, **plot_grid_dict, )

    # Display the plot in the main section
    st.pyplot(fig)
    return cap_factors

def even_more_results(dataframe: pd.DataFrame):
    st.write(dataframe.describe())



def main():
    # # Reading cutout for given year:
    @st.cache_resource()
    def load_cutout():
        cutout = atlite.Cutout("../data/weather/western-europe-2011.nc")
        cutout.prepare()
        return cutout

    cutout = load_cutout()

    url = "https://tubcloud.tu-berlin.de/s/7bpHrAkjMT3ADSr/download/country_shapes.geojson"

    @st.cache_data()
    def load_countries():
        return gpd.read_file(url).set_index("name")

    countries = load_countries()
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
    cells = cutout.grid

    evaluation, graphs = st.columns([1, 2])
    (
        location,
        turbine,
        upper_lower,
        other_countries_connection,
    ) = select_location_and_turbine(countries=countries)
    with evaluation:
        power_yield = power_time_series(cutout, turbine, location=location)
        duration = duration_curve(power_yield, duration_col="Power in MW")
        distance = get_distance_to_coast(countries=countries, point=location.point, toggle=other_countries_connection)
        lcoe = calc_lcoe(capacity=turbine.capacity,
                         power_yield=power_yield.sum()["Power in MW"],
                         distance=distance,
                         depth=location.depth,
                         value=upper_lower)
        st.write(f"Depth at location is: {round(location.depth)} m")
        st.write(f"Distance to coast is: {round(distance)} km")
        st.write(
            f"Lcoe at location is: {round(lcoe, 3)} €/MWh"\
            f" or {round(lcoe/10, 3)} ct/kWh")
        st.write(f"Energy Production at location is: {round(power_yield.sum()['Power in MW'], 3)} MWh")
        st.write(f"The Turbine is not Producing Energy for {round(duration['Power in MW'].value_counts()[0]/87.60, 3)} \
                    % of the year")
        with st.expander("Additional evaluation"):
            even_more_results(power_yield.loc[:, "Power in MW"])
    with graphs:
        location_specific, global_specific = st.tabs(
            ["Location Specific", "Global Turbine specific"]
        )

        with location_specific:
            st.title(
                "Single Turbine at Given location"
            )
            topografic.print_depth_map(location)
            st.line_chart(data=power_yield, x="date", y=["Power in MW"])

            st.line_chart(
                data=duration,
                x="percentage",
                y=["Power in MW"],
            )

        with global_specific:
            st.title(
                "Lcoe and Energy yield for a single Turbine global level"
            )
            production = color_map(turbine, cutout, cells, plot_grid_dict, projection)
            #
            heat_map(
                turbine,
                production,
                cells,
                plot_grid_dict,
                projection,
                location,
                other_countries_connection,
                upper_lower,
            )
        # pydeck(heat)


if __name__ == "__main__":
    main()
