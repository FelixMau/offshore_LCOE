import shapely.geometry
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


def chose_windturbine():
    turbine = Turbine(
        name=st.selectbox(
            "Chose Windturbine",
            (
                "Bonus_B1000_1000kW",
                "Enercon_E101_3000kW",
                "Enercon_E126_7500kW",
                "Enercon_E82_3000kW",
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

def select_location():
    st.sidebar.title("Coordinates")
    x = st.sidebar.number_input("X coordinate", value=3.0)
    y = st.sidebar.number_input("Y coordinate", value=54.0)
    return topografic.Location(x=x, y=y, countries=countries)



def main():
    # Reading cutout for given year:

    cutout = atlite.Cutout("../data/weather/western-europe-2011-01.nc")
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



    cap_factors = color_map(turbine.name, cutout, cells, plot_grid_dict, projection)  #

    location = select_location()
    power_time_series(cutout, turbine, location=location)

    topografic.print_depth_map(location)


if __name__ == "__main__":
    main()
