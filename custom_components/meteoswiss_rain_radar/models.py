from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RadarState:
    rain: bool
    distance_km: float | None
    radar_file: str
    updated: datetime