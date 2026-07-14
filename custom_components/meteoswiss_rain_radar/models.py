from dataclasses import dataclass
from datetime import datetime

from .radar import RadarData


@dataclass(slots=True)
class RadarResult:
    radar: RadarData
    rain: bool
    distance_km: float | None
    updated: datetime