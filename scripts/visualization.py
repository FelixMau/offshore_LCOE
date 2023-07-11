from cartopy.crs import PlateCarree as plate
import cartopy.crs as ccrs
import geopandas as gpd
import atlite
import streamlit as st
import topografic
from energyharvest import energy_yield, Turbine, power_time_series, duration_curve
from topografic import Location, get_distance_to_coast
from lcoe import calc_lcoe_from_series, calc_lcoe
import matplotlib.pyplot as plt
import rasterstats as rs
import numpy as np
import os
import pandas as pd
import time


def select_location_and_turbine(countries):
    st.sidebar.title("Settings")
    x = st.sidebar.number_input("Longitude", value=6.81)
    y = st.sidebar.number_input("Latitude", value=53.98)
    numer_of_turbines = st.sidebar.number_input("How many Windturbines would you like to install?", value=54)
    turbine = Turbine.from_beautiful_name(
        name=st.sidebar.selectbox(
            "Chose Windturbine",
            (
                "NREL Reference Turbine 10MW",
                "NREL Reference Turbine 6MW",
                "NREL Reference Turbine 8MW",
                "NREL Reference Turbine 12MW",
                "NREL Reference Turbine 15MW",
                "NREL Reference Turbine 12MW (2020 ATB)",
                "NREL Reference Turbine 15MW (2020 ATB)",
                "NREL Reference Turbine 18MW (2020 ATB)",
                "NREL Reference Turbine 5MW",
                "Vestas V112 3MW",
                "Vestas V164 7MW",
            ),
        ),
        number_of_turbines=numer_of_turbines
    )
    upper_lower = {"Pessimistic": "upper", "Optimistic": "lower"}[
        st.sidebar.selectbox("Mode of Projection", ("Pessimistic", "Optimistic"))
    ]
    other_countries_connection = st.sidebar.selectbox(
        "Allow connection to other countries",
        ("Yes, all countries", "No, only to Germany"),
    )
    read_from_disk = st.sidebar.checkbox("Read lcoe results from Disk?", value=True)
    if other_countries_connection == "Yes, all countries":
        other_countries_connection = True
    else:
        other_countries_connection = False

    with st.sidebar.expander("Info on Settings"):
        st.write(
            "`Longitude`: Sets Longitude (x value) of Location for Turbine and Location specific evaluation. "
            "Does not interfere with 'Global' values"
        )

        st.write(
            "`Latitude`: Sets Latitude (y value) of Location for Turbine and Location specific evaluation. "
            "Does not interfere with 'Global' values"
        )

        st.write(
            "`Chose Windturbine`: Select Wind-turbine from atlite Turbine datasets"
        )

        st.write(
            "`Mode of Projection`: Determines whether optimistic or pessimistic Values are chosen for"
            "prices and Lifetimes in 2025"
        )

        st.write(
            "`Allow connection to other countries`: Defines if connections to other countries than Germany "
            "are allowed. Influences the `Distance` value"
        )

    return (
        Location(x=x, y=y, countries=countries),
        turbine,
        upper_lower,
        other_countries_connection,
        read_from_disk,
        numer_of_turbines
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
    read_from_disk: bool = True,
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
    filename = f"../data/figs/{turbine.name}_{other_countries_connection}_{value}_{turbine.number_of_turbines}.shp"

    if os.path.isfile(filename) and read_from_disk:
        cap_factors = gpd.read_file(filename).set_index(keys=["y", "x"])
    else:
        start_time = time.time()
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

        st.markdown("Calculating your new lcoe Heatmap!")

        progress_bar = st.progress(0)
        cap_factors.reset_index()
        cap_factors["depth"] = [x["mean"] for x in stats]
        cap_factors["index"] = cap_factors.reset_index().index
        result = cap_factors.apply(
            calc_lcoe_from_series,
            axis=1,
            **{
                "capacity": turbine.capacity,
                "countries": location.countries,
                "other_countries_connection": other_countries_connection,
                "value": value,
                "progress": progress_bar,
                "number_of_values": len(cap_factors)
            },
        )

        cap_factors["lcoe"] = result.str[
            0
        ]  # Assuming the calculated LCOE is the first value in the result
        cap_factors["distance"] = result.str[
            1
        ]  # Assuming the distance is the second value in the result
        cap_factors.to_file(filename)
        end_time = time.time()
        st.write(f"Calculation took: {end_time-start_time} seconds ")

    cap_factors.rename(columns={"lcoe": "lcoe [€_MWh]"}, inplace=True)  #
    limit = cap_factors.sort_values(by="lcoe [€_MWh]", ascending=False).iloc[10][
        "lcoe [€_MWh]"
    ]
    cap_factors_xarray = cap_factors.to_xarray()["lcoe [€_MWh]"]

    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))
    cap_factors_xarray.plot(ax=ax, transform=plate(), vmax=limit, levels=10)

    cells.plot(
        ax=ax,
        **plot_grid_dict,
    )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Show axis ticks
    x_ticks = cells.x[::5]
    y_ticks = cells.y[::5]
    plt.xticks(np.arange(min(x_ticks), max(x_ticks), 1.0))
    plt.yticks(np.arange(min(y_ticks), max(y_ticks), 1.0))
    fig.tight_layout()
    st.pyplot(fig)
    return cap_factors


def even_more_results(dataframe: pd.DataFrame):
    st.write(dataframe.describe())


def main():
    st.set_page_config(layout="wide")
    # # Reading cutout for given year:
    @st.cache_resource()
    def load_cutout():

        cutout = atlite.Cutout(
            "../data/weather/western-europe-2011.nc",
        )
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
        read_from_disk,
        number_of_turbines
    ) = select_location_and_turbine(countries=countries)
    with evaluation:
        power_yield = power_time_series(cutout, turbine, location=location)
        duration = duration_curve(power_yield, duration_col="Power in MW")
        distance = get_distance_to_coast(
            countries=countries, point=location.point, toggle=other_countries_connection
        )
        lcoe, costs = calc_lcoe(
            capacity=turbine.capacity,
            power_yield=power_yield.sum()["Power in MW"],
            distance=distance,
            depth=location.depth,
            value=upper_lower,
        )
        st.write(f"Depth at location is: {round(location.depth)} m")
        st.write(f"Distance to coast is: {round(distance)} km")
        st.write(
            f"Lcoe at location is: {round(lcoe, 3)} €/MWh"
            f" or {round(lcoe/10, 3)} ct/kWh"
        )
        st.write(
            f"Energy Production at location is: {round(power_yield.sum()['Power in MW'], 3)} MWh"
        )
        st.write(
            f"The Turbine is not Producing Energy for {round(duration['Power in MW'].value_counts()[0]/87.60, 3)} \
                    % of the year"
        )
        st.write(
            f"The Turbine(park) has an average capacity factor of \
            {round(100*power_yield.sum()['Power in MW']/(turbine.capacity*len(power_yield)), 1)} % over the year"
        )
    with graphs:
        location_specific, global_specific = st.tabs(
            ["Location Specific", "Global Turbine specific"]
        )

        with location_specific:
            st.title("Single Turbine at Given location")
            topografic.print_depth_map(location)
            st.line_chart(data=power_yield, x="date", y=["Power in MW"])

            st.line_chart(
                data=duration,
                x="percentage",
                y=["Power in MW"],
            )
            st.title("Capex and Opex")
            fig, ax = plt.subplots()
            #explode = [0,0,0.1,0,0,0.1]
            ax.pie(costs[1:], autopct='%1.f%%',
                   #explode=explode,
                   textprops ={"fontsize": 8})
            ax.set_aspect("equal")
            ax.legend(costs.index[1:], loc='upper left', fontsize="x-small", bbox_to_anchor=(-0.3, 1))
            st.pyplot(fig)

        with global_specific:
            st.title("Lcoe and Energy yield for a single Turbine global level")
            production = energy_yield(
                turbine, cutout, cells, plot_grid_dict, projection
            )
            #
            heat_cap_factors = heat_map(
                turbine,
                production,
                cells,
                plot_grid_dict,
                projection,
                location,
                other_countries_connection,
                upper_lower,
                read_from_disk=read_from_disk,
            )
            with st.expander("Best locations for Turbine"):
                df = heat_cap_factors.drop(columns=["lon", "lat", "geometry"])
                df.rename(index={"x": "Longitude", "y": "Latitude"}, inplace=True)
                df.rename(
                    columns={
                        "x": "Longitude",
                        "y": "Latitude",
                        "distance": "distance [m]",
                        "depth": "depth[m]",
                        "Generation": "Generation [MWh]",
                    },
                    inplace=True,
                )
                st.write(df.sort_values(by="lcoe [€_MWh]").head(5))
                st.download_button(
                    label="Download data as CSV",
                    data=df.to_csv(),
                    file_name=f"lcoe_{turbine}.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
