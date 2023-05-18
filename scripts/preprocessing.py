from feedinlib.powerplants import WindPowerPlant
from feedinlib.powerplants import get_power_plant_data

from feedinlib.open_FRED import Weather


from shapely.geometry import Point

# plot wind speed
import matplotlib.pyplot as plt



# get wind turbines
turbine_df = get_power_plant_data(dataset='oedb_turbine_library')
# print the first four turbines
turbine_df.iloc[1:5, :]


# set up wind turbine using the wind turbine library
turbine_data = {
    'turbine_type': 'E-101/3050',  # turbine name as in turbine library
    'hub_height': 135  # in m
    }
wind_turbine = WindPowerPlant(**turbine_data)

# specify latitude and longitude of wind turbine location
location = Point(13.5, 52.4)

# download weather data for June 2017
open_FRED_weather_data = Weather(
    start='2017-06-01', stop='2017-07-01',
    locations=[location],
    heights=[140, 160],
    variables="windpowerlib",
    **defaultdb())

# get weather data in windpowerlib format
weather_df = open_FRED_weather_data.df(location=location, lib="windpowerlib")


# plot wind speed
weather_df.loc[:, ['wind_speed']].plot(title='Wind speed')
plt.xlabel('Time')
plt.ylabel('Wind speed in m/s')
plt.plot()