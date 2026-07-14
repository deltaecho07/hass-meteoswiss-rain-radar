from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from custom_components.meteoswiss_rain_radar.coordinator import (
	SwissRainRadarCoordinator,
)


@pytest.fixture
def entry() -> SimpleNamespace:
	return SimpleNamespace(
		data={
			"latitude": 47.3769,
			"longitude": 8.5417,
			"radius": 5.0,
			"threshold": 0.2,
		}
	)


@pytest.fixture
def coordinator(entry) -> SwissRainRadarCoordinator:
	hass = Mock()
	return SwissRainRadarCoordinator(hass=hass, entry=entry)


@pytest.mark.asyncio
async def test_async_initialize_refreshes_and_schedules(coordinator):
	coordinator.async_refresh = AsyncMock()
	coordinator._schedule_next = Mock()

	await coordinator.async_initialize()

	coordinator.async_refresh.assert_awaited_once()
	coordinator._schedule_next.assert_called_once_with()


@pytest.mark.asyncio
async def test_scheduled_refresh_calls_async_refresh(coordinator):
	coordinator.async_refresh = AsyncMock()

	await coordinator._scheduled_refresh(now=datetime(2026, 1, 1, tzinfo=UTC))

	coordinator.async_refresh.assert_awaited_once()


def test_schedule_replaces_existing_listener(coordinator):
	old_remove = Mock()
	new_remove = Mock()
	coordinator._remove_listener = old_remove
	when = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

	with patch(
		"custom_components.meteoswiss_rain_radar.coordinator.async_track_point_in_utc_time",
		return_value=new_remove,
	) as mock_track:
		coordinator._schedule(when)

	old_remove.assert_called_once_with()
	mock_track.assert_called_once_with(
		coordinator.hass,
		coordinator._scheduled_refresh,
		when,
	)
	assert coordinator._remove_listener is new_remove


def test_expected_timestamp_rounds_down_to_5_minutes(coordinator):
	fixed_now = datetime(2026, 7, 14, 10, 23, 48, 123456, tzinfo=UTC)

	with patch(
		"custom_components.meteoswiss_rain_radar.coordinator.datetime"
	) as mock_datetime:
		mock_datetime.now.return_value = fixed_now
		result = coordinator._expected_timestamp()

	assert result == datetime(2026, 7, 14, 10, 20, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_async_update_data_skips_when_filename_unchanged(coordinator):
	ts = datetime(2026, 7, 14, 10, 20, tzinfo=UTC)
	coordinator._expected_timestamp = Mock(return_value=ts)
	coordinator._last_filename = "same-file.h5"
	coordinator.data = {"cached": True}
	coordinator._schedule = Mock()

	coordinator.downloader.build_url = Mock(return_value=("same-file.h5", "url"))
	coordinator.downloader.radar_exists = AsyncMock()

	result = await coordinator._async_update_data()

	assert result == {"cached": True}
	coordinator.downloader.radar_exists.assert_not_called()
	coordinator._schedule.assert_called_once_with(ts + timedelta(minutes=5, seconds=20))


@pytest.mark.asyncio
async def test_async_update_data_retries_when_radar_missing(coordinator):
	ts = datetime(2026, 7, 14, 10, 20, tzinfo=UTC)
	now = datetime(2026, 7, 14, 10, 21, tzinfo=UTC)
	coordinator._expected_timestamp = Mock(return_value=ts)
	coordinator._last_filename = None
	coordinator.data = {"cached": "value"}
	coordinator._schedule = Mock()

	coordinator.downloader.build_url = Mock(return_value=("new-file.h5", "url"))
	coordinator.downloader.radar_exists = AsyncMock(return_value=False)

	with patch(
		"custom_components.meteoswiss_rain_radar.coordinator.datetime"
	) as mock_datetime:
		mock_datetime.now.return_value = now
		result = await coordinator._async_update_data()

	assert result == {"cached": "value"}
	coordinator.downloader.radar_exists.assert_awaited_once_with(ts)
	coordinator._schedule.assert_called_once_with(now + timedelta(seconds=15))


@pytest.mark.asyncio
async def test_async_update_data_fetches_detects_and_returns_result(coordinator):
	ts = datetime(2026, 7, 14, 10, 20, tzinfo=UTC)
	radar = SimpleNamespace(filename="fresh-file.h5")

	coordinator._expected_timestamp = Mock(return_value=ts)
	coordinator._last_filename = None
	coordinator._schedule = Mock()

	coordinator.downloader.build_url = Mock(return_value=("fresh-file.h5", "url"))
	coordinator.downloader.radar_exists = AsyncMock(return_value=True)
	coordinator.downloader.fetch = AsyncMock(return_value=radar)
	coordinator.detector.detect = Mock(return_value=(True, 1.5))

	with patch(
		"custom_components.meteoswiss_rain_radar.coordinator.RadarResult",
		side_effect=lambda **kwargs: kwargs,
	):
		result = await coordinator._async_update_data()

	coordinator.downloader.radar_exists.assert_awaited_once_with(ts)
	coordinator.downloader.fetch.assert_awaited_once_with(ts)
	coordinator.detector.detect.assert_called_once_with(
		radar=radar,
		latitude=47.3769,
		longitude=8.5417,
		radius_km=5.0,
		threshold=0.2,
	)
	assert coordinator._last_filename == "fresh-file.h5"
	coordinator._schedule.assert_called_once_with(ts + timedelta(minutes=5, seconds=20))
	assert result == {
		"radar": radar,
		"rain": True,
		"distance_km": 1.5,
	}
