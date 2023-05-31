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



def plot_power_curve(cutout, turbine, cells, plot_grid_dict, projection, point: shapely.geometry.Point, cap_factors):
    sites = gpd.GeoDataFrame(
        [
            [f"{turbine}", point.x, point.y, 10],
        ],
        columns=["name", "x", "y", "capacity"],
    ).set_index("name")
    cells_generation = sites.merge(cells, how="inner").rename(pd.Series(sites.index))

    layout = (
        xr.DataArray(cells_generation.set_index(["y", "x"]).capacity.unstack())
        .reindex_like(cap_factors)
        .rename("Installed Capacity [MW]")
    )
    fig, ax = plt.subplots(1, figsize=(9, 4))
    power_generation = cutout.wind(
        turbine, layout=layout, shapes=cells_generation.geometry
    )

    power_generation.to_pandas().plot(subplots=True, ax=ax)
    ax.set_xlabel("date")
    ax.set_ylabel("Generation [MW]")
    fig.tight_layout()
    st.pyplot(fig)

