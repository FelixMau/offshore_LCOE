from cartopy.crs import PlateCarree as plate
import matplotlib.pyplot as plt
import atlite
from atlite.resource import windturbines
import streamlit as st
import pandas as pd
from topografic import Location
import dataclasses
import yaml
import numpy as np


def energy_yield(turbine, cutout, cells, plot_grid_dict, projection):
    cap_factors = (
        cutout.wind(turbine=turbine.name, capacity_factor=False) * turbine.capacity
    )

    fig, ax = plt.subplots(subplot_kw={"projection": projection}, figsize=(9, 7))
    cap_factors.name = "Generation in MWh"
    cap_factors.plot(ax=ax, transform=plate())
    cells.plot(ax=ax, **plot_grid_dict)

    # Add x and y axis labels
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Show axis ticks
    x_ticks = cells.x[::5]
    y_ticks = cells.y[::5]
    plt.xticks(np.arange(min(x_ticks), max(x_ticks), 1.0))
    plt.yticks(np.arange(min(y_ticks), max(y_ticks), 1.0))
    fig.tight_layout()
    # Display the plot in the main section
    st.pyplot(fig)
    return cap_factors


@dataclasses.dataclass
class Turbine:
    name: str
    capacity: float = dataclasses.field(init=False)

    @classmethod
    def from_beautiful_name(cls, name):
        name = {
            "NREL Reference Turbine 10MW": "NREL_ReferenceTurbine_2016CACost_10MW_offshore",
            "NREL Reference Turbine 6MW": "NREL_ReferenceTurbine_2016CACost_6MW_offshore",
            "NREL Reference Turbine 8MW": "NREL_ReferenceTurbine_2016CACost_8MW_offshore",
            "NREL Reference Turbine 12MW": "NREL_ReferenceTurbine_2019ORCost_12MW_offshore",
            "NREL Reference Turbine 15MW": "NREL_ReferenceTurbine_2019ORCost_15MW_offshore",
            "NREL Reference Turbine 12MW (2020 ATB)": "NREL_ReferenceTurbine_2020ATB_12MW_offshore",
            "NREL Reference Turbine 15MW (2020 ATB)": "NREL_ReferenceTurbine_2020ATB_15MW_offshore",
            "NREL Reference Turbine 18MW (2020 ATB)": "NREL_ReferenceTurbine_2020ATB_18MW_offshore",
            "NREL Reference Turbine 5MW": "NREL_ReferenceTurbine_5MW_offshore",
            "Vestas V112 3MW": "Vestas_V112_3MW_offshore",
            "Vestas V164 7MW": "Vestas_V164_7MW_offshore",
        }[name]
        return cls(name=name)

    def __post_init__(self):
        with open(windturbines.get(self.name), "r") as f:
            data = yaml.safe_load(f)
        self.capacity = max(data["POW"])

    def beauty_string(self):
        beauty_name = ""
        for idx, split in enumerate(self.name.split("_")):
            if (
                any(element.isdigit() for element in split) or split == "offshore"
            ) and idx > 1:
                continue
            else:
                beauty_name += " " + split
        return beauty_name + " " + str(self.capacity) + "MW"


def power_time_series(
    cutout: atlite.Cutout, turbine: Turbine | list, location: Location
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
        # st.line_chart(timeseries)
        timeseries.rename(columns={0: "Power in MW"}, inplace=True)
        timeseries.loc[:, "date"] = timeseries.index
        return timeseries


def duration_curve(timeseries, duration_col):
    timeseries.loc[:, "interval"] = 1
    timeseries_sorted = timeseries.sort_values(by=duration_col, ascending=False)
    timeseries_sorted.reset_index(drop=True, inplace=True)
    timeseries_sorted.loc[:, "duration"] = timeseries_sorted.loc[:, "interval"].cumsum()
    timeseries_sorted.loc[:, "percentage"] = (
        timeseries_sorted.loc[:, "duration"] * 100 / len(timeseries_sorted["duration"])
    )

    return timeseries_sorted
