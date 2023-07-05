import atlite
i = 1
full_cutout = atlite.Cutout(
    path=f"../data/weather/western-europe-2011-{i}.nc",
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
    path=f"../data/weather/western-europe-2011-{i}.nc",
    module="era5",
    x=slice(3.6913, 18),
    y=slice(52, 61),
    time=f"2011-{i}",
    )
    cutout.prepare()
    full_cutout = full_cutout.merge(other=cutout)

full_cutout.prepare()

