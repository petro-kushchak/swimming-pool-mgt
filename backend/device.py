from typing import Optional

import httpx

from logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 10.0


class FilteringDevice:
    _client: httpx.AsyncClient | None = None

    def __init__(
        self,
        name: str,
        start_url: str,
        stop_url: str,
        status_url: Optional[str] = None,
    ):
        self.name = name
        self.start_url = start_url
        self.stop_url = stop_url
        self.status_url = status_url

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        return cls._client

    @classmethod
    async def close_client(cls) -> None:
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None

    async def start(self) -> bool:
        try:
            client = await self.get_client()
            response = await client.post(self.start_url)
            success = response.status_code in (200, 201, 202, 204)
            if success:
                logger.info("Device started", device=self.name, url=self.start_url)
            else:
                logger.warning("Device start failed", device=self.name, status=response.status_code)
            return success
        except httpx.HTTPError as e:
            logger.error("Device start error", device=self.name, error=str(e))
            return False

    async def stop(self) -> bool:
        try:
            client = await self.get_client()
            response = await client.post(self.stop_url)
            success = response.status_code in (200, 201, 202, 204)
            if success:
                logger.info("Device stopped", device=self.name, url=self.stop_url)
            else:
                logger.warning("Device stop failed", device=self.name, status=response.status_code)
            return success
        except httpx.HTTPError as e:
            logger.error("Device stop error", device=self.name, error=str(e))
            return False

    async def get_status(self) -> Optional[str]:
        if not self.status_url:
            return None
        try:
            client = await self.get_client()
            response = await client.get(self.status_url)
            if response.status_code == 200:
                return response.text.strip()
        except httpx.HTTPError as e:
            logger.error("Device status error", device=self.name, error=str(e))
        return None


def create_device(config: dict | None) -> Optional[FilteringDevice]:
    if not config:
        return None
    return FilteringDevice(
        name=config.get("name", "Unknown"),
        start_url=config["start_url"],
        stop_url=config["stop_url"],
        status_url=config.get("status_url"),
    )
