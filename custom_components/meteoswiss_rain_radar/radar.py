from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import h5py
import numpy as np

from .geo import wgs84_to_grid


@dataclass(slots=True)
class RadarData:
    rain_mask: np.ndarray
    ul_x: int
    ul_y: int
    scale: int

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        threshold: float = 0.2,
    ) -> RadarData:
        if isinstance(data, BytesIO):
            data.seek(0)
            h5_data = data
        else:
            h5_data = BytesIO(data)

        with h5py.File(h5_data, "r") as h5:

            radar = h5["dataset1/data1/data"][:]

            where = h5["where"]

            ul_lon = float(where.attrs["UL_lon"])
            ul_lat = float(where.attrs["UL_lat"])

            scale = int(where.attrs["xscale"])

            ul_x, ul_y = wgs84_to_grid(
                ul_lat,
                ul_lon,
            )

            rain_mask = radar.astype(np.float32) > threshold

        return cls(
            rain_mask=rain_mask,
            ul_x=ul_x,
            ul_y=ul_y,
            scale=scale,
        )