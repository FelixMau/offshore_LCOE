from shapely.geometry import Point
from cartopy.crs import PlateCarree as plate
import cartopy.crs as ccrs
import geopandas as gpd
import atlite
import streamlit as st
import topografic
import rasterio
from rasterio.plot import show
from PIL import Image
from energyharvest import color_map, power_time_series, Turbine
from topografic import Location
from lcoe import calc_lcoe_from_series, calc_lcoe
import matplotlib.pyplot as plt
import pandas as pd
import rasterstats as rs

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

def heat_map(turbine, cutout, cells, plot_grid_dict, projection, location):
    cap_factors = cutout.wind(turbine=turbine.name, capacity_factor=False)
    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))

    cap_factors = gpd.GeoDataFrame(cap_factors.to_dataframe(),
                                   geometry=gpd.points_from_xy(cap_factors.to_dataframe().lon,
                                                               cap_factors.to_dataframe().lat))

    stats = rs.zonal_stats(cells.geometry, location.depth_dataset.read(1), affine=location.depth_dataset.transform,
                   stats=["mean"])
    cap_factors.reset_index()
    cap_factors["depth"] = [x['mean'] for x in stats]
    cap_factors.apply(calc_lcoe_from_series, axis=1, **{"capacity":turbine.capacity})

    cap_factors.name = "Capacity Factor"
    cap_factors.plot(ax=ax, transform=plate())
    cells.plot(ax=ax, **plot_grid_dict)
    fig.tight_layout()

    # Display the plot in the main section
    st.pyplot(fig)
    return cap_factors


def main():
    # Reading cutout for given year:

    cutout = atlite.Cutout("../data/weather/western-europe-2011.nc")
    cutout.prepare()

    url = "https://tubcloud.tu-berlin.de/s/7bpHrAkjMT3ADSr/download/country_shapes.geojson"
    countries = gpd.read_file(url).set_index("name")
    projection = ccrs.PlateCarree()

    plot_grid_dict = dict(
        alpha=0.1,
        edgecolor="k",
        zorder=4,
        aspect="equal",
        facecolor="None",
        transform=plate(),
    )

    # Add a title to your app
    st.title("Wind Data Visualization")

    turbine = chose_windturbine()

    cells = cutout.grid

    cap_factors = color_map(turbine.name, cutout, cells, plot_grid_dict, projection)

    location = select_location(countries=countries)
    power_yield = power_time_series(cutout, turbine, location=location)

    depth = topografic.print_depth_map(location)

    st.write(calc_lcoe(capacity=turbine.capacity, power_yield=power_yield, distance =10, depth =20, value= "lower"))
    heat_map(turbine, cutout, cells, plot_grid_dict, projection, location)


if __name__ == "__main__":
    main()
