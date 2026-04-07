import os
import httpx
from typing import Optional

DEFAULT_TIMEOUT = 10

class FilteringDevice:
    def __init__(self, name: str, start_url: str, stop_url: str, status_url: Optional[str] = None):
        self.name = name
        self.start_url = start_url
        self.stop_url = stop_url
        self.status_url = status_url

    async def start(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(self.start_url)
                return response.status_code in (200, 201, 202, 204)
        except Exception as e:
            print(f"Failed to start device {self.name}: {e}")
            return False

    async def stop(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(self.stop_url)
                return response.status_code in (200, 201, 202, 204)
        except Exception as e:
            print(f"Failed to stop device {self.name}: {e}")
            return False

    async def get_status(self) -> Optional[str]:
        if not self.status_url:
            return None
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.get(self.status_url)
                if response.status_code == 200:
                    return response.text.strip()
        except Exception as e:
            print(f"Failed to get device {self.name} status: {e}")
        return None

def create_device(config: dict) -> Optional[FilteringDevice]:
    if not config:
        return None
    return FilteringDevice(
        name=config.get("name", "Unknown"),
        start_url=config["start_url"],
        stop_url=config["stop_url"],
        status_url=config.get("status_url")
    )
