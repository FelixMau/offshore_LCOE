import pandas as pd



def calc_lcoe(capacity=1, power_yield=1, distance =1, depth =1, value= "lower"):

    tech = pd.read_csv("../data/lcoe/tech_data.csv", index_col=0)
    depth = -1*depth
    # calculate capex costs
    # Turbine
    capex_turbine = (tech.loc["Nominal investment (equipment: turbines) [M€/MW_e]"][value]+tech.loc["Nominal investment (installation: turbines) [M€/MW_e]"][value])*capacity*1e6
    # Foundation
    if depth < 40 and distance < 30:    # Monopile
        capex_found = tech.loc["Nominal investment (equipment + installation: foundation monopile) [M€/MW_e]"][value] * capacity * 1e6

    elif (depth > 40 and depth < 60) and (distance > 30 and distance < 90): # Tripod
        capex_found = tech.loc["Nominal investment (equipment+installation: foundation Tripod) [M€/MW_e]"][value] * capacity * 1e6
    else: # Floating
        capex_found = tech.loc["Nominal investment (equipment+installation: foundation floating) [M€/MW_e]"][value] * capacity * 1e6

    # array cables
    capex_array = (tech.loc["Nominal investment (equipment: array cables) [M€/MW]"][value]+tech.loc["Nominal investment (installation: array cables) [M€/MW]"][value])*capacity * 1e6
    # grid connection
    capex_export = tech.loc["Nominal investment (equipment+installation: grid connection) [M€/km]"][value] * distance * 1e6
    # Planning
    capex_project = tech.loc["Nominal investment (Project development etc.) [M€/MW_e]"][value]*1e6
    # Sum total capex
    capex = capex_project+capex_export+capex_array+capex_turbine+capex_found
    # calculate annuity factor
    wacc = tech.loc["WACC_real [%]"][value] / 100
    af = (wacc * pow((1 + wacc),tech.loc["Technical lifetime [years]"][value]))/(pow((1+wacc),tech.loc["Technical lifetime [years]"][value])-1)
    # calculate OPEX
    opex = (tech.loc["Fixed O&M [€/MW_e/y]"][value]*capacity+tech.loc["Variable O&M [€/MWh_e]"][value]*power_yield)
    # calculate lcoe
    lcoe = ((capex*af)+opex)/power_yield

    return lcoe

def calc_lcoe_from_series(row: pd.Series, capacity: float = 1, distance = 1, value:str = "lower")->float:
    """
    Takes a pandas series to calculate lcoe based on given series and its index.
    :return:
    """
    #Index(['lon', 'lat', 'specific generation', 'geometry'], dtype='object')
    # ToDo: add distance once it is implemented to this call
    return calc_lcoe(power_yield=row['specific generation'], capacity=capacity, depth=row["depth"], distance=distance, value=value)