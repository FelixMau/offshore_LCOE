import pandas as pd


def calc_lcoe(capacity=1, power_yield=1, distance =1, depth =1, af=1, turbine = 1):

    tech = pd.read_csv("data/lcoe/tech_data.csv", index_col=0)

    capacity = turbine.capacity ## get from energyharvest
    power_yield = timeseries.sum()  # get from energyharvest
    distance = get_distance_to_coast(self)  # get from this function
    depth = water_depth(depth_map=depth_map, depth=depth_map[row, col]) # get frpm this function

    # calculate capex costs
    # Turbine
    capex_turbine = (tech.loc["Nominal investment (equipment: turbines) [M€/MW_e]"]+tech.loc["Nominal investment (installation: turbines) [M€/MW_e]"])*capacity*1e6
    # Foundation
    if depth < 20 and distance < 30:    # Monopile
        capex_found = (tech.loc["Nominal investment (equipment: foundation) [M€/MW_e]"] + tech.loc[
            "Nominal investment (installation: foundation) [M€/MW_e]"]) * capacity * 1e6

    elif (depth > 20 and depth < 30) and (distance > 30 and distance < 90): # Tripod
        capex_found = 0
    elif (depth > 30 and depth < 90) and distance < 20: # Floating
        capex_found = 0
    else:   # Not suitable for offshore
        capex_found = 0
    # array cables
    capex_array = (tech.loc["Nominal investment (equipment: array cables) [M€/MW]"]+tech.loc["Nominal investment (installation: array cables) [M€/MW]"])*capacity * 1e6
    # grid connection
    capex_export = tech.loc["Nominal investment (equipment+installation: grid connection) [M€/km]"] * distance * 1e6
    # Planning
    capex_project = tech.loc["Nominal investment (Project development etc.) [M€/MW_e]"]*1e6
    # Sum total capex
    capex = capex_project+capex_export+capex_array+capex_turbine+capex_found
    # calculate annuity factor
    wacc = tech.loc["WACC_real [%]"] / 100
    af = wacc / (1 - pow((1 + wacc), -tech.loc["Technical lifetime [years]"]))
    # calculate OPEX
    opex = (tech.loc["Fixed O&M [€/MW_e/y]"]*capacity+tech.loc["Variable O&M [€/MWh_e]"]*power_yield)
    # calculate lcoe
    lcoe = ((capex*af)+opex)/power_yield

    return lcoe
