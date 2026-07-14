from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .detector import RainDetector
from .radar_downloader import RadarDownloader
from .models import RadarResult

_LOGGER = logging.getLogger(__name__)

class SwissRainRadarCoordinator(
    DataUpdateCoordinator[RadarResult]
):

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ):
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
        )
        self.entry = entry
        self.downloader = RadarDownloader()
        self.detector = RainDetector()
        self._last_filename = None
        self._remove_listener = None


    async def async_initialize(self):
        await self.async_refresh()
        self._schedule_next()
    

    def _schedule(
      self,
      when: datetime,
      ):
      if self._remove_listener:
        self._remove_listener()

      self._remove_listener = async_track_point_in_utc_time(
        self.hass,
        self._scheduled_refresh,
        when,
      )
    

    async def _scheduled_refresh(
      self,
      now,
      ) -> None:
      await self.async_refresh()

    
    def _expected_timestamp(self):
      now = datetime.now(UTC)

      minute = (now.minute // 5) * 5

      return now.replace(
        minute=minute,
        second=0,
        microsecond=0,
        tzinfo=UTC,
        )
    
    async def _async_update_data(self):
      timestamp = self._expected_timestamp()

      filename, _ = self.downloader.build_url(timestamp)
      
      if filename == self._last_filename:
        self._schedule(
            timestamp + timedelta(minutes=5, seconds=20)
        )
        return self.data
      
      if not await self.downloader.radar_exists(timestamp):
        self._schedule(
            datetime.now(UTC) + timedelta(seconds=15)
        )
        return self.data
      
      radar = await self.downloader.fetch(timestamp)
      self._last_filename = radar.filename

      rain, distance = self.detector.detect(
        radar=radar,
        latitude=self.entry.data["latitude"],
        longitude=self.entry.data["longitude"],
        radius_km=self.entry.data["radius"],
        threshold=self.entry.data["threshold"],
      )

      self._schedule(
        timestamp + timedelta(minutes=5, seconds=20)
      )

      return RadarResult(
        radar=radar,
        rain=rain,
        distance_km=distance,
      )