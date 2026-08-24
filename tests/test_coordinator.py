"""Tests for MeteoSwissRainRadarCoordinator.

Requires: pip install pytest pytest-asyncio pytest-freezer
          pytest-homeassistant-custom-component

Adjust the import below to match your actual module path, e.g.:
    from custom_components.meteoswiss_rain_radar.coordinator import (
        MeteoSwissRainRadarCoordinator,
    )
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss_rain_radar.const import (
    CONF_RADIUS,
    CONF_THRESHOLD,
    DOMAIN,
)
from custom_components.meteoswiss_rain_radar.coordinator import (
    MeteoSwissRainRadarCoordinator,
)

MODULE = "custom_components.meteoswiss_rain_radar.coordinator"


def make_entry(**data_overrides) -> MockConfigEntry:
    data = {
        CONF_THRESHOLD: 0.2,
        CONF_RADIUS: 10,
        "latitude": 47.0,
        "longitude": 7.5,
    }
    data.update(data_overrides)
    return MockConfigEntry(domain=DOMAIN, data=data, options={})


@pytest.fixture
def coordinator(hass):
    entry = make_entry()
    entry.add_to_hass(hass)
    with patch(f"{MODULE}.RadarDownloader"), patch(f"{MODULE}.RainDetector"):
        coord = MeteoSwissRainRadarCoordinator(hass, entry)
    # Replace with fresh AsyncMocks so we can assert on individual tests.
    coord.downloader = MagicMock()
    coord.downloader.close = AsyncMock()
    coord.downloader.radar_exists = AsyncMock()
    coord.downloader.fetch_radar = AsyncMock()
    coord.downloader.build_url = MagicMock(
        return_value=("some.h5", "https://example.com/some.h5")
    )
    coord.detector = MagicMock()
    return coord


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_init_sets_up_attributes(hass):
    entry = make_entry()
    entry.add_to_hass(hass)

    with patch(f"{MODULE}.RadarDownloader"), patch(f"{MODULE}.RainDetector"):
        coord = MeteoSwissRainRadarCoordinator(hass, entry)

    assert coord.entry is entry
    assert coord.name == DOMAIN
    assert coord._remove_listener is None


# ---------------------------------------------------------------------------
# start / stop
# ---------------------------------------------------------------------------


def test_start_schedules_next_update(coordinator):
    with patch.object(coordinator, "_schedule_next_update") as mock_schedule:
        coordinator.start()

    mock_schedule.assert_called_once_with()


@pytest.mark.asyncio
async def test_stop_closes_downloader_and_removes_listener(coordinator):
    remove_listener = MagicMock()
    coordinator._remove_listener = remove_listener

    await coordinator.stop()

    coordinator.downloader.close.assert_awaited_once()
    remove_listener.assert_called_once()
    assert coordinator._remove_listener is None


@pytest.mark.asyncio
async def test_stop_without_listener_does_not_raise(coordinator):
    coordinator._remove_listener = None

    await coordinator.stop()

    coordinator.downloader.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# _schedule_next_update
# ---------------------------------------------------------------------------


def test_schedule_next_update_retry_adds_15_seconds(coordinator, freezer):
    now = datetime(2024, 1, 1, 10, 7, 30, tzinfo=UTC)
    freezer.move_to(now)

    with patch(f"{MODULE}.async_track_point_in_utc_time") as mock_track:
        coordinator._schedule_next_update(retry=True)

    expected_when = now + timedelta(seconds=15)
    mock_track.assert_called_once_with(
        coordinator.hass, coordinator._scheduled_refresh, expected_when
    )
    assert coordinator._remove_listener is mock_track.return_value


def test_schedule_next_update_rounds_up_to_next_5_minutes(coordinator, freezer):
    now = datetime(2024, 1, 1, 10, 7, 30, tzinfo=UTC)
    freezer.move_to(now)

    with patch(f"{MODULE}.async_track_point_in_utc_time") as mock_track:
        coordinator._schedule_next_update()

    expected_when = now.replace(minute=10, second=50, microsecond=0)
    mock_track.assert_called_once_with(
        coordinator.hass, coordinator._scheduled_refresh, expected_when
    )


def test_schedule_next_update_rolls_over_to_next_hour(coordinator, freezer):
    # minute=57 -> (57 // 5 + 1) * 5 == 60 -> should roll into the next hour.
    now = datetime(2024, 1, 1, 10, 57, 0, tzinfo=UTC)
    freezer.move_to(now)

    with patch(f"{MODULE}.async_track_point_in_utc_time") as mock_track:
        coordinator._schedule_next_update()

    expected_when = now.replace(minute=0, second=50, microsecond=0) + timedelta(hours=1)
    mock_track.assert_called_once_with(
        coordinator.hass, coordinator._scheduled_refresh, expected_when
    )


def test_schedule_next_update_cancels_existing_listener(coordinator, freezer):
    freezer.move_to(datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC))
    old_listener = MagicMock()
    coordinator._remove_listener = old_listener

    with patch(f"{MODULE}.async_track_point_in_utc_time"):
        coordinator._schedule_next_update()

    old_listener.assert_called_once()


# ---------------------------------------------------------------------------
# _scheduled_refresh
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scheduled_refresh_calls_async_refresh(coordinator):
    with patch.object(
        coordinator, "async_refresh", new_callable=AsyncMock
    ) as mock_refresh:
        await coordinator._scheduled_refresh(datetime.now(UTC))

    mock_refresh.assert_awaited_once()


# ---------------------------------------------------------------------------
# _expected_timestamp
# ---------------------------------------------------------------------------


def test_expected_timestamp_floors_to_5_minutes(coordinator, freezer):
    freezer.move_to(datetime(2024, 1, 1, 10, 7, 42, 123456, tzinfo=UTC))

    result = coordinator._expected_timestamp()

    assert result == datetime(2024, 1, 1, 10, 5, 0, 0, tzinfo=UTC)


def test_expected_timestamp_at_exact_5_minute_mark(coordinator, freezer):
    freezer.move_to(datetime(2024, 1, 1, 10, 10, 0, tzinfo=UTC))

    result = coordinator._expected_timestamp()

    assert result == datetime(2024, 1, 1, 10, 10, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# _async_update_data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_update_data_raises_when_radar_not_yet_available(coordinator):
    coordinator.downloader.radar_exists.return_value = False

    with patch.object(coordinator, "_schedule_next_update") as mock_schedule:
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    mock_schedule.assert_called_once_with(retry=True)
    coordinator.downloader.fetch_radar.assert_not_awaited()


@pytest.mark.asyncio
async def test_async_update_data_success_uses_options_over_data(coordinator):
    coordinator.hass.config_entries.async_update_entry(
        coordinator.entry, options={CONF_THRESHOLD: 0.5, CONF_RADIUS: 20}
    )
    coordinator.downloader.radar_exists.return_value = True
    radar_bytesio = BytesIO(b"raw-bytes")
    coordinator.downloader.fetch_radar.return_value = radar_bytesio

    fake_radar_data = MagicMock(name="RadarData")
    coordinator.detector.detect.return_value = (True, 3.5)

    with (
        patch.object(coordinator, "_schedule_next_update") as mock_schedule,
        patch(f"{MODULE}.RadarData") as mock_radar_data_cls,
    ):
        mock_radar_data_cls.from_bytes.return_value = fake_radar_data

        result = await coordinator._async_update_data()

    mock_radar_data_cls.from_bytes.assert_called_once_with(radar_bytesio, threshold=0.5)
    coordinator.detector.detect.assert_called_once_with(
        fake_radar_data,
        latitude=47.0,
        longitude=7.5,
        radius_km=20,
    )
    mock_schedule.assert_called_once_with()

    assert result.radar is fake_radar_data
    assert result.rain is True
    assert result.distance_km == 3.5


@pytest.mark.asyncio
async def test_async_update_data_success_falls_back_to_entry_data(coordinator):
    # options empty -> should fall back to entry.data values
    coordinator.hass.config_entries.async_update_entry(coordinator.entry, options={})
    coordinator.downloader.radar_exists.return_value = True
    radar_bytesio = BytesIO(b"raw-bytes")
    coordinator.downloader.fetch_radar.return_value = radar_bytesio
    coordinator.detector.detect.return_value = (False, None)

    with (
        patch.object(coordinator, "_schedule_next_update"),
        patch(f"{MODULE}.RadarData") as mock_radar_data_cls,
    ):
        mock_radar_data_cls.from_bytes.return_value = MagicMock()

        await coordinator._async_update_data()

    mock_radar_data_cls.from_bytes.assert_called_once_with(radar_bytesio, threshold=0.2)
    coordinator.detector.detect.assert_called_once_with(
        mock_radar_data_cls.from_bytes.return_value,
        latitude=47.0,
        longitude=7.5,
        radius_km=10,
    )
