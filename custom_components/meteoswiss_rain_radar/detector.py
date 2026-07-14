import math

from .geo import wgs84_to_grid
from .radar import RadarData


class RainDetector:

    def detect(
        self,
        radar: RadarData,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> tuple[bool, float | None]:

        gx, gy = wgs84_to_grid(latitude, longitude)

        gx = int((gx - radar.ul_x) / radar.scale)
        gy = int((radar.ul_y - gy) / radar.scale)

        cells = math.ceil(radius_km)

        nearest = None

        for dy in range(-cells, cells + 1):
            for dx in range(-cells, cells + 1):

                if math.sqrt(dx * dx + dy * dy) > cells:
                    continue

                xx = gx + dx
                yy = gy + dy

                if (
                    xx < 0
                    or yy < 0
                    or yy >= radar.rain_mask.shape[0]
                    or xx >= radar.rain_mask.shape[1]
                ):
                    continue

                if radar.rain_mask[yy, xx]:

                    distance = math.sqrt(dx * dx + dy * dy)

                    if nearest is None or distance < nearest:
                        nearest = distance

        if nearest is None:
            return False, None

        return True, round(nearest, 2)