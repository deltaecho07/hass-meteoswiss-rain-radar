from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.const import UnitOfLength
from .const import DOMAIN

from .entity import MeteoSwissRainRadarEntity

class DistanceSensor(
    MeteoSwissRainRadarEntity,
    SensorEntity,
):

    _attr_name = "Distance"

    _attr_native_unit_of_measurement = (
        UnitOfLength.KILOMETERS
    )

    def __init__(
        self,
        coordinator,
        entry,
    ):
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{entry.entry_id}_distance"
        )
    
    @staticmethod
    async def async_setup_entry(hass, entry, async_add_entities):
        coordinator = hass.data[DOMAIN][entry.entry_id]

        async_add_entities(
            [
                DistanceSensor(
                    coordinator,
                    entry,
                )
            ]
        )

    @property
    def native_value(self):
        return self.coordinator.data.distance_km