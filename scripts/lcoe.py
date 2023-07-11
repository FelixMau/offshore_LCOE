from typing import Tuple, Any

import pandas as pd
from topografic import is_location_offshore, get_distance_to_coast
import geopandas as gpd
import streamlit as st

@st.cache_data()
def read_tech_and_cable_data():
    cables = {
        'max capacity': [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500],
        'Offshore substations': [1, 2, 2, 2, 3, 3, 4, 4, 4, 5],
        'Export cables': [1, 2, 3, 3, 4, 5, 6, 6, 7, 8]
    }

    tech = pd.read_csv("../data/lcoe/tech_data.csv", index_col=0)

    cables = pd.DataFrame(cables)
    return tech, cables


def choose_export_cables(capacity)->int:
    df = read_tech_and_cable_data()[1]

    # Prompt the user for the input capacity

    # Filter the DataFrame to find the number of export cables
    filtered_df = df[df['max capacity'] > capacity]
    num_export_cables = filtered_df['Export cables'].iloc[0]
    num_arrays = filtered_df['Offshore substations'].iloc[0]
    return num_export_cables, num_arrays

def calc_lcoe(capacity: float, power_yield: float, distance: float, depth: float, value: str="lower"):
    """
    # Todo: Check units
    :param capacity: Capacity of Turbine in MW
    :param power_yield: power yield for whole year in MWh
    :param distance: distance to coast in m
    :param depth: depth at location in m
    :param value: decision variable whether to use upper, middle or lower bounds
                where lower is meant in terms of low cost
    :return:
    """

    tech = read_tech_and_cable_data()[0]
    # calculate capex costs
    # Turbine
    capex_turbine = (
        (
            tech.loc["Nominal investment (equipment: turbines) [M€/MW_e]"][value]
            + tech.loc["Nominal investment (installation: turbines) [M€/MW_e]"][value]
        )
        * capacity
        * 1e6
    )
    # Foundation
    if depth < 20:  # Monopile
        capex_found = (
            tech.loc[
                "Nominal investment (equipment + installation: foundation monopile) [M€/MW_e]"
            ][value]
            * capacity
            * 1e6
        )

    elif depth > 20 and depth < 40:  # Tripod
        capex_found = (
            tech.loc[
                "Nominal investment (equipment + installation: foundation jacket) [M€/MW_e]"
            ][value]
            * capacity
            * 1e6
        )
    else:  # Floating
        capex_found = (
            tech.loc[
                "Nominal investment (equipment+installation: foundation floating) [M€/MW_e]"
            ][value]
            * capacity
            * 1e6
        )

    number_of_cables, num_arrays = choose_export_cables(capacity=capacity)

    # array cables
    capex_array = (
            (
                    tech.loc["Nominal investment (equipment: array cables) [M€/MW]"][value]
                    + tech.loc["Nominal investment (installation: array cables) [M€/MW]"][value]
            )
            * capacity
            * 1e6
    )

    # grid connection
    capex_export = (
        tech.loc[
            "Nominal investment (equipment+installation: grid connection) [M€/km]"
        ][value]
        *number_of_cables
        * distance
        * 1e6
    )

    # Planning
    capex_project = (
        tech.loc["Nominal investment (Project development etc.) [M€/MW_e]"][value] * 1e6
    )
    # Sum total capex
    capex = capex_project + capex_export + capex_array + capex_turbine + capex_found
    # calculate annuity factor
    wacc = tech.loc["WACC_real [%]"][value] / 100
    af = (wacc * pow((1 + wacc), tech.loc["Technical lifetime [years]"][value])) / (
        pow((1 + wacc), tech.loc["Technical lifetime [years]"][value]) - 1
    )
    # calculate OPEX
    opex = (
        tech.loc["Fixed O&M [€/MW_e/y]"][value] * capacity
        + tech.loc["Variable O&M [€/MWh_e]"][value] * power_yield
    )
    # calculate lcoe
    lcoe = ((capex * af) + opex) / power_yield
    return lcoe, pd.Series({
                "Name": "Capex and Opex",
                "Capex_Turbine": capex_turbine,
                "Capex_Foundation": capex_found,
                "Capex_Array_Cables": capex_array,
                "Capex_Grid_Connection": capex_export,
                "Capex_Planning": capex_project,
                "Opex": opex,
                })


def calc_lcoe_from_series(
    row: pd.Series,
    capacity: float,
    countries: gpd.GeoDataFrame,
    value: str = "lower",
    other_countries_connection: bool = True,
    progress: st.progress = None,
    number_of_values: int = 1
) -> tuple[float | Any, float] | None:
    """
    Takes a pandas series to calculate lcoe based on given series and its index.
    :return:
    """

    offshore = is_location_offshore(countries=countries, point=row["geometry"])
    if progress:
        progress.progress(row["index"] / number_of_values)
    if offshore:
        distance = get_distance_to_coast(
            countries=countries,
            point=row["geometry"],
            toggle=other_countries_connection,
        )
        return (
            calc_lcoe(
                power_yield=row["Generation in MWh"],
                capacity=capacity,
                depth=row["depth"],
                distance=distance,
                value=value,
            )[0],
            distance,
        )
    else:
        return None
