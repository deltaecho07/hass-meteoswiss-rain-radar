from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.components.sensor import SensorDeviceClass

from .entity import MeteoSwissRainRadarEntity

class LastUpdateSensor(
    MeteoSwissRainRadarEntity,
    SensorEntity,
):
  _attr_name = "Last Update"

  _attr_device_class = SensorDeviceClass.TIMESTAMP

  def __init__(self, coordinator, entry):
    super().__init__(coordinator, entry)
    self._attr_unique_id = f"{entry.entry_id}_last_radar"

  @property
  def native_value(self):
     return self.coordinator.data.last_update if self.coordinator.data is not None else None