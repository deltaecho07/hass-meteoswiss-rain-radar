"""Tests for RadarDownloader.

Requires: pip install pytest pytest-asyncio pytest-httpx

"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO

import httpx
import pytest

from custom_components.meteoswiss_rain_radar.radar_downloader import RadarDownloader
from custom_components.meteoswiss_rain_radar.const import METEOSWISS_API_BASE_URL


# A fixed timestamp used across tests so the generated filename/url is deterministic.
TEST_DT = datetime(2024, 3, 5, 14, 30)  # 2024, day-of-year 065 (%j), 14:30
EXPECTED_FILENAME = "rzc240651430nl.001.h5"
EXPECTED_URL = f"{METEOSWISS_API_BASE_URL}20240305-ch/{EXPECTED_FILENAME}"


@pytest.fixture
async def downloader():
    """Provide a RadarDownloader instance and clean up its client afterwards."""
    dl = RadarDownloader()
    yield dl
    await dl.close()


# ---------------------------------------------------------------------------
# Pure helper methods - no HTTP involved
# ---------------------------------------------------------------------------

def test_build_filename():
    filename = RadarDownloader.build_filename(TEST_DT)
    assert filename == EXPECTED_FILENAME


def test_build_url():
    filename, url = RadarDownloader.build_url(TEST_DT)
    assert filename == EXPECTED_FILENAME
    assert url == EXPECTED_URL


# ---------------------------------------------------------------------------
# radar_exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_radar_exists_true(downloader, httpx_mock):
    httpx_mock.add_response(
        method="HEAD",
        url=EXPECTED_URL,
        status_code=200,
    )

    exists = await downloader.radar_exists(TEST_DT)

    assert exists is True
    request = httpx_mock.get_requests()[0]
    assert request.headers["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_radar_exists_false(downloader, httpx_mock):
    httpx_mock.add_response(
        method="HEAD",
        url=EXPECTED_URL,
        status_code=404,
    )

    exists = await downloader.radar_exists(TEST_DT)

    assert exists is False


# ---------------------------------------------------------------------------
# fetch_radar
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_radar_success(downloader, httpx_mock):
    fake_content = b"fake-h5-binary-data"
    httpx_mock.add_response(
        method="GET",
        url=EXPECTED_URL,
        status_code=200,
        content=fake_content,
    )

    result = await downloader.fetch_radar(TEST_DT)

    assert isinstance(result, BytesIO)
    assert result.read() == fake_content
    request = httpx_mock.get_requests()[0]
    assert request.headers["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_fetch_radar_raises_on_http_error(downloader, httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=EXPECTED_URL,
        status_code=500,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await downloader.fetch_radar(TEST_DT)