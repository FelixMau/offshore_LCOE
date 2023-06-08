import shapely.geometry
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
import topografic
import rasterio
from rasterio.plot import show
from PIL import Image
from topografic import Location


def color_map(turbine, cutout, cells, plot_grid_dict, projection):
    cap_factors = cutout.wind(turbine=turbine, capacity_factor=True)

    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))
    cap_factors.name = "Capacity Factor"
    cap_factors.plot(ax=ax, transform=plate())
    cells.plot(ax=ax, **plot_grid_dict)
    fig.tight_layout()

    # Display the plot in the main section
    st.pyplot(fig)
    return cap_factors


def power_time_series(
    cutout: atlite.Cutout, turbine: topografic.Turbine | list, location: Location
):
    """
    Plotting timeseries for given Turbine at given location

    :param cutout: atlite.Cutout with winddata
    :param turbine:
    :param location:
    :return:
    """
    if isinstance(turbine, list):
        # Todo: subplots for multiple locations
        pass
    else:
        fig, ax = plt.subplots(1, figsize=(15, 10))
        timeseries = cutout.wind(
            turbine=turbine.name,
            layout=cutout.layout_from_capacity_list(
                data=pd.DataFrame(
                    {
                        "x": [location.x],
                        "y": [location.y],
                        "Capacity": [turbine.capacity],
                    }
                )
            ),
        ).to_pandas()
        timeseries.plot(ax=ax)
        ax.set_xlabel("MW")
        st.pyplot(fig=fig)

        return timeseries.sum()
