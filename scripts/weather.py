import atlite
import os

"""
Downloading Weather Data using atlite API to ERA5
"""

i = 1
weather_path = os.path.join(os.getcwd(), "..", "data", "weather")
full_cutout = atlite.Cutout(
    path=os.path.join(weather_path, f"western-europe-2011-{i}.nc"),
    module="era5",
    x=slice(3.6913, 18),
    y=slice(52, 61),
    time=f"2011-{i}",
    )
full_cutout.prepare()

for i in range(2,13):
    if i < 10:
        i = f"0{i}"
    cutout = atlite.Cutout(
    path=os.path.join(weather_path, f"western-europe-2011-{i}.nc"),
    module="era5",
    x=slice(3.6913, 18),
    y=slice(52, 61),
    time=f"2011-{i}",
    )
    cutout.prepare()
    full_cutout = full_cutout.merge(other=cutout)
full_cutout.prepare()

full_cutout.to_file(os.path.join(weather_path, "western-europe-2011.nc"))