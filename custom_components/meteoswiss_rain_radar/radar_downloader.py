from __future__ import annotations
from datetime import datetime
from io import BytesIO
import httpx

from .const import METEOSWISS_API_BASE_URL

class RadarDownloader:
  def __init__(self):
    self._client = None
  
  async def close(self):
    if self._client:
      await self._client.aclose()

  @staticmethod
  def build_filename(dt: datetime) -> str:
        year = dt.strftime("%y")
        day = dt.strftime("%j")
        time = dt.strftime("%H%M")

        return f"rzc{year}{day}{time}vl.001.h5"
  
  @staticmethod
  def build_url(
        timestamp: datetime,
    ) -> tuple[str, str]:
    folder = timestamp.strftime("%Y%m%d")
    filename = RadarDownloader.build_filename(timestamp)
    url = (
       METEOSWISS_API_BASE_URL
       + folder + "-ch/"
       + filename)
    return filename, url

  async def radar_exists(
        self,
        timestamp: datetime,
    ) -> bool:
    _, url = self.build_url(timestamp)
    if not self._client:
      self._client = httpx.AsyncClient(timeout=30)
    response = await self._client.head(url,headers={"Cache-Control": "no-cache"})
    return response.status_code == 200
  
  async def fetch_radar(
        self,
        timestamp: datetime,
    ) -> BytesIO:
    _, url = self.build_url(timestamp)
    if not self._client:
      self._client = httpx.AsyncClient(timeout=30)
    response = await self._client.get(url,headers={"Cache-Control": "no-cache"})
    response.raise_for_status()
    return BytesIO(response.content)