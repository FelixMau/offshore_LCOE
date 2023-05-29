from cartopy.crs import PlateCarree as plate
import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib.pyplot as plt
import atlite
import streamlit as st
import yaml
from yaml.loader import SafeLoader
import xarray as xr
import pandas as pd


def color_map(turbine, cutout, cells, plot_grid_dict, projection):
    cap_factors = cutout.wind(turbine=turbine, capacity_factor=True)

    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))
    cap_factors.name = "Capacity Factor"
    cap_factors.plot(ax=ax, transform=plate())
    cells.plot(ax=ax, **plot_grid_dict)
    fig.tight_layout()

    # Display the plot in the main section
    st.pyplot(fig)

def main():
    # Reading cutout for given year:

    cutout = atlite.Cutout(
        "/home/felix/PycharmProjects/offshore_LCOE/scripts/western-europe-2011-01.nc"

    )
    cutout.prepare()

    url = "https://tubcloud.tu-berlin.de/s/7bpHrAkjMT3ADSr/download/country_shapes.geojson"
    countries = gpd.read_file(url).set_index('name')
    crs = ccrs.PlateCarree()
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
    turbine = st.selectbox("Chose Windturbine",
                 ("Bonus_B1000_1000kW",
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
                    ))

    cells = cutout.grid

    color_map(turbine, cutout, cells, plot_grid_dict, projection)






if __name__ == "__main__":
    main()


