from homeassistant.const import Platform

DOMAIN = "meteoswiss_rain_radar"
VERSION = "0.1.0"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

DEFAULT_RADIUS = 5.0
DEFAULT_THRESHOLD = 0.2

CONF_RADIUS = "radius"
CONF_THRESHOLD = "threshold"

METEOSWISS_API_BASE_URL = (
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-radar-precip/"
)