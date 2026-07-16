from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)

from .entity import MeteoSwissRainRadarEntity


class RainBinarySensor(
    MeteoSwissRainRadarEntity,
    BinarySensorEntity,
):

    _attr_name = "Rain"

    def __init__(
        self,
        coordinator,
        entry,
    ):
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{entry.entry_id}_rain"
        )

    @property
    def is_on(self):
        return self.coordinator.data.rain