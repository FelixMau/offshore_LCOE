import dataclasses
import cartopy.crs as ccrs
import geopandas as gpd


@dataclasses.dataclass
class location():
    x: float
    y: float
    crs: ccrs
    countries: gpd.GeoDataFrame
    projection: ccrs
    depth_map: gpd.GeoDataFrame
    waterdepth: float = dataclasses.field(init=False)
    ground_material: str = dataclasses.field(init=False)


    def __post_init__(self):
        get_water_depth(self.x, self.y, self.depth_map)
        gebco = rasterio.open('/home/felix/PycharmProjects/offshore_LCOE/data/gebco_2023_n61.0_s51.0_w3.0_e18.0.nc')
        band = gebco.read(1)
        np.unique(band)
        show(band)


@dataclasses.dataclass
class turbine():
    name: str
    capacity: float






