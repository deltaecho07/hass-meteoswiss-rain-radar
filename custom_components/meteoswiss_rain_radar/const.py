DOMAIN = "meteoswiss_rain_radar"
VERSION = "0.1.0"

PLATFORMS = [
    "binary_sensor",
    "sensor",
]

DEFAULT_RADIUS = 5.0
DEFAULT_THRESHOLD = 0.2

CONF_RADIUS = "radius"
CONF_THRESHOLD = "threshold"

METEOSWISS_API_BASE_URL = (
    "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-precip/items"
)