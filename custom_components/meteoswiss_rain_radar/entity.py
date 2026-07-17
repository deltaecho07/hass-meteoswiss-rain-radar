from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN


class MeteoSwissRainRadarEntity(
    CoordinatorEntity,
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry,
    ):
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self._entry.entry_id,
                )
            },
            name="MeteoSwiss Rain Radar",
            manufacturer="MeteoSwiss",
            model="Radar Rain Detection",
            configuration_url="https://github.com/deltaecho07/hass-meteoswiss-rain-radar'",
        )

    @property
    def available(self):
        return self.coordinator.last_update_success