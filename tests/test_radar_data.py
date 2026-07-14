from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

import h5py
import numpy as np
import pytest

from custom_components.meteoswiss_rain_radar.radar import RadarData

# Patch target: wgs84_to_grid is imported into the radar_data module's namespace,
# so it must be patched there (not in .geo) to actually take effect.
WGS84_TO_GRID_PATH = "custom_components.meteoswiss_rain_radar.radar.wgs84_to_grid"


def _build_fake_h5_bytes(
    radar_array: np.ndarray,
    ul_lon: float,
    ul_lat: float,
    xscale: int,
) -> bytes:
    """Build a minimal in-memory HDF5 file matching MeteoSwiss's radar layout."""
    buffer = BytesIO()
    with h5py.File(buffer, "w") as h5:
        h5.create_dataset("dataset1/data1/data", data=radar_array)
        where = h5.create_group("where")
        where.attrs["UL_lon"] = ul_lon
        where.attrs["UL_lat"] = ul_lat
        where.attrs["xscale"] = xscale
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def fake_radar_bytes() -> bytes:
    radar_array = np.array([[0.0, 0.5], [0.1, 0.9]], dtype=np.float32)
    return _build_fake_h5_bytes(radar_array, ul_lon=7.5, ul_lat=47.0, xscale=1)


def test_from_bytes_parses_metadata_and_applies_threshold(fake_radar_bytes):
    with patch(WGS84_TO_GRID_PATH, return_value=(123, 456)) as mock_grid:
        result = RadarData.from_bytes("test.h5", fake_radar_bytes, threshold=0.2)

    # wgs84_to_grid must be called with (lat, lon), matching the source order.
    mock_grid.assert_called_once_with(47.0, 7.5)

    assert result.filename == "test.h5"
    assert result.ul_x == 123
    assert result.ul_y == 456
    assert result.scale == 1

    # threshold=0.2, comparison is strictly ">" -> 0.2 itself would be False
    expected_mask = np.array([[False, True], [False, True]])
    np.testing.assert_array_equal(result.rain_mask, expected_mask)


def test_from_bytes_default_threshold(fake_radar_bytes):
    with patch(WGS84_TO_GRID_PATH, return_value=(0, 0)):
        result = RadarData.from_bytes("test.h5", fake_radar_bytes)

    assert result.rain_mask.dtype == np.bool_


def test_from_bytes_threshold_boundary_is_exclusive():
    # Value exactly at the threshold should NOT count as rain (">" not ">=").
    radar_array = np.array([[0.2, 0.20001]], dtype=np.float32)
    data = _build_fake_h5_bytes(radar_array, ul_lon=8.0, ul_lat=46.5, xscale=1)

    with patch(WGS84_TO_GRID_PATH, return_value=(0, 0)):
        result = RadarData.from_bytes("boundary.h5", data, threshold=0.2)

    np.testing.assert_array_equal(result.rain_mask, np.array([[False, True]]))


def test_from_bytes_uses_correct_scale():
    radar_array = np.zeros((2, 2), dtype=np.float32)
    data = _build_fake_h5_bytes(radar_array, ul_lon=8.0, ul_lat=46.5, xscale=500)

    with patch(WGS84_TO_GRID_PATH, return_value=(0, 0)):
        result = RadarData.from_bytes("scale.h5", data)

    assert result.scale == 500
    assert isinstance(result.scale, int)
