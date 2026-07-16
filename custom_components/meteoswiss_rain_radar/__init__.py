from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import MeteoSwissRainRadarCoordinator

type MeteoSwissRainRadarConfigEntry = ConfigEntry[MeteoSwissRainRadarCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeteoSwissRainRadarConfigEntry,
) -> bool:
    """Set up MeteoSwiss Rain Radar."""

    coordinator = MeteoSwissRainRadarCoordinator(
        hass,
        entry,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    coordinator.start()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: MeteoSwissRainRadarConfigEntry,
) -> bool:
    coordinator = entry.runtime_data
    await coordinator.stop()
    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )