from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
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
    
    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.distance_km

class LastUpdateSensor(
    MeteoSwissRainRadarEntity,
    SensorEntity,
):
  _attr_name = "Last Radar Image"

  _attr_device_class = SensorDeviceClass.TIMESTAMP

  def __init__(self, coordinator, entry):
    super().__init__(coordinator, entry)
    self._attr_unique_id = f"{entry.entry_id}_last_radar"

  @property
  def native_value(self):
     return self.coordinator.data.last_update if self.coordinator.data is not None else None


async def async_setup_entry(hass, entry, async_add_entities):
  coordinator = hass.data[DOMAIN][entry.entry_id]

  async_add_entities(
    [
      DistanceSensor(
      coordinator,
      entry,
      ),
      LastUpdateSensor(
        coordinator,
        entry,
      ),
    ]
  )