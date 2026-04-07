from datetime import datetime
from typing import Optional
from status import get_pool_status as calc_status
from device import FilteringDevice, create_device

class PoolStatus:
    def __init__(self, pool_id: int, name: str, schedule: list, device: Optional[FilteringDevice] = None):
        self.pool_id = pool_id
        self.name = name
        self.schedule = schedule
        self.device = device
        self.manual_override: Optional[str] = None
        self.last_action: Optional[datetime] = None
        self.action_by: Optional[str] = None
        self._device_running: bool = False

    def get_status(self) -> dict:
        if self.manual_override:
            if self.manual_override == "running":
                return {
                    "filtering": True,
                    "manual_override": True,
                    "device_controlled": self.device is not None,
                    "device_running": self._device_running,
                    "started_at": self.last_action.isoformat() if self.last_action else None,
                    "started_by": self.action_by,
                    "ends_at": None,
                    "remaining_minutes": None,
                    "next_filter": None,
                    "last_filtered": None
                }
            else:
                return {
                    "filtering": False,
                    "manual_override": True,
                    "device_controlled": self.device is not None,
                    "device_running": self._device_running,
                    "stopped_at": self.last_action.isoformat() if self.last_action else None,
                    "stopped_by": self.action_by,
                    "next_filter": None,
                    "last_filtered": self.last_action.strftime("%H:%M") if self.last_action else None
                }
        
        return calc_status(self.schedule)

    async def start_filtering(self, by: str = "manual") -> bool:
        self.manual_override = "running"
        self.last_action = datetime.now()
        self.action_by = by
        
        if self.device:
            self._device_running = await self.device.start()
            return self._device_running
        return True

    async def stop_filtering(self, by: str = "manual") -> bool:
        self.manual_override = "stopped"
        self.last_action = datetime.now()
        self.action_by = by
        
        if self.device:
            self._device_running = not await self.device.stop()
            return not self._device_running
        return True

    def clear_override(self):
        self.manual_override = None


_pool_statuses: dict[int, PoolStatus] = {}

def init_pool_statuses(pools: list):
    _pool_statuses.clear()
    for pool in pools:
        device = create_device(pool.get("device"))
        status = PoolStatus(pool["id"], pool["name"], pool.get("schedule"), device)
        _pool_statuses[pool["id"]] = status

def get_pool_status_by_id(pool_id: int) -> Optional[PoolStatus]:
    return _pool_statuses.get(pool_id)

def get_all_pool_statuses() -> dict[int, PoolStatus]:
    return _pool_statuses
