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

import pandas as pd



def select_location_and_turbine(countries):
    st.sidebar.title("Settings")
    x = st.sidebar.number_input("X coordinate", value=3.0)
    y = st.sidebar.number_input("Y coordinate", value=54.0)
    turbine = Turbine.from_beautiful_name(
        name=st.sidebar.selectbox(
            "Chose Windturbine",
            ("NREL Reference Turbine 10MW",
            "NREL Reference Turbine 6MW",
            "NREL Reference Turbine 8MW",
            "NREL Reference Turbine 12MW",
            "NREL Reference Turbine 15MW",
            "NREL Reference Turbine 12MW (2020 ATB)",
            "NREL Reference Turbine 15MW (2020 ATB)",
            "NREL Reference Turbine 18MW (2020 ATB)",
            "NREL Reference Turbine 5MW",
            "Vestas V112 3MW",
            "Vestas V164 7MW"),
        ),
    )
    upper_lower = st.sidebar.selectbox("Upper, lower values?", ("upper", "lower"))
    other_countries_connection = st.sidebar.checkbox(
        "Allow connection to other countries", value=True
    )
    with st.sidebar.expander("More Settings"):
        factor_for_distance = st.sidebar.number_input("Chose a distance factor", value=1.0)
        cuto_off_heat_map_limit = st.sidebar.text_input("Where should the Heatmap price be cutoff? Or set `auto`")

        st.write("The Distance factor is reducing the Distance itself, therefore 'Distance' is no more correct"
                     "if a different factor to 1 is chosen."
                     "This is to mimic deploying larger windparks where distance might have lower impact.")
    return (
        Location(x=x, y=y, countries=countries),
        turbine,
        upper_lower,
        other_countries_connection,
        factor_for_distance,
        cuto_off_heat_map_limit
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
    distance_factor: float = 1,
        cut_off_limit: str = "auto"
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
            "distance_factor": distance_factor

        },
    )
    cap_factors.rename(columns={"lcoe": "lcoe [€/MWh]"}, inplace=True)  #
    if cut_off_limit != "auto":


        limit = cap_factors.sort_values(by="lcoe [€/MWh]", ascending=False).iloc[10][
        "lcoe [€/MWh]"
        ]
    else:
        try:
            limit = float(cut_off_limit)
        except:
            limit = 100

    cap_factors = cap_factors.to_xarray()["lcoe [€/MWh]"]

    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))
    cap_factors.plot(ax=ax, transform=plate(), vmax=limit)

    cells.plot(
        ax=ax,
        **plot_grid_dict,
    )
    # Display the plot in the main section
    st.pyplot(fig)
    return cap_factors


def even_more_results(dataframe: pd.DataFrame):
    st.write(dataframe.describe())


def main():
    st.set_page_config(layout="wide")
    # # Reading cutout for given year:
    @st.cache_resource()
    def load_cutout():

        cutout = atlite.Cutout("../data/weather/western-europe-2011.nc", )
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
        distance_factor,
        cut_off_heat_map_limit
    ) = select_location_and_turbine(countries=countries)
    with evaluation:
        power_yield = power_time_series(cutout, turbine, location=location)
        duration = duration_curve(power_yield, duration_col="Power in MW")
        distance = get_distance_to_coast(
            countries=countries, point=location.point, toggle=other_countries_connection, factor=distance_factor
        )
        lcoe = calc_lcoe(
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
        with st.expander("Additional evaluation"):
            even_more_results(power_yield.loc[:, "Power in MW"])
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

        with global_specific:
            st.title("Lcoe and Energy yield for a single Turbine global level")
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
                distance_factor,
                cut_off_limit=cut_off_heat_map_limit
            )
        # pydeck(heat)


if __name__ == "__main__":
    main()
