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

from .const import DOMAIN, CONF_RADIUS, CONF_THRESHOLD
from .detector import RainDetector
from .radar_downloader import RadarDownloader
from .models import RadarResult

_LOGGER = logging.getLogger(__name__)

class MeteoSwissRainRadarCoordinator(
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

    def start(self):
        self._schedule_next_update()

    def stop(self):
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    def _schedule_next_update(
      self,
      retry: bool = False,
      ):

      if self._remove_listener:
        self._remove_listener()

      now = datetime.now(UTC)

      if retry:
        when = now + timedelta(seconds=15)

      else:
        minute = ((now.minute // 5) + 1) * 5
        if minute == 60:
          when = now.replace(
              minute=0,
              second=20,
              microsecond=0,
          ) + timedelta(hours=1)
        else:
          when = now.replace(
              minute=minute,
              second=20,
              microsecond=0,
          )

      _LOGGER.debug(
        "Next radar update: %s",
        when,
        )

      self._remove_listener = async_track_point_in_utc_time(
        self.hass,
        self._scheduled_refresh,
        when,
      )
    
    async def _scheduled_refresh(
    self,
    now,
    ):
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
    
    async def _async_update_data(
      self,
    ) -> RadarResult:
      timestamp = self._expected_timestamp()
      if not await self.downloader.radar_exists(
        timestamp,
      ):
        self._schedule_next_update(
            retry=True,
        )
        return self.data
      radar = await self.downloader.fetch_radar(timestamp)
      self._last_filename = radar.filename

      rain, distance = self.detector.detect(
        radar,
        latitude=self.entry.data["latitude"],
        longitude=self.entry.data["longitude"],
        radius_km=self.entry.options.get(
            CONF_RADIUS,
            self.entry.data[CONF_RADIUS],
        ),
        threshold=self.entry.options.get(
            CONF_THRESHOLD,
            self.entry.data[CONF_THRESHOLD],
        ),
      )
      self._schedule_next_update()
      return RadarResult(
        radar=radar,
        rain=rain,
        distance_km=distance,
      )