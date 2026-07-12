from pyproj import Transformer

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2056",
    always_xy=True
)

def wgs84_to_grid(lat: float, lon: float):
    x, y = transformer.transform(lon, lat)
    return int(x), int(y)