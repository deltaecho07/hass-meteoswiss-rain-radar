from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)

from .const import DOMAIN
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
    
    @staticmethod
    async def async_setup_entry(hass, entry, async_add_entities):
        coordinator = hass.data[DOMAIN][entry.entry_id]

        async_add_entities(
            [
                RainBinarySensor(
                    coordinator,
                    entry,
                )
            ]
        )

    @property
    def is_on(self):
        return self.coordinator.data.rain