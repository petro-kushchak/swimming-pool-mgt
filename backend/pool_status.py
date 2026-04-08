from datetime import datetime, timedelta
from typing import Optional
from status import get_pool_status as calc_status
from device import FilteringDevice, create_device
from utils import parse_time, parse_duration


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
        self._scheduled_end_time: Optional[datetime] = None

    def _calculate_remaining_time(self) -> tuple[Optional[str], Optional[int]]:
        if not self.last_action or not self.schedule:
            return None, None

        if self._scheduled_end_time:
            now = datetime.now()
            if now < self._scheduled_end_time:
                remaining = (self._scheduled_end_time - now).total_seconds() / 60
                end_str = self._scheduled_end_time.strftime("%H:%M")
                return end_str, int(remaining)
            return None, 0

        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute

        for entry in self.schedule:
            start_h, start_m = parse_time(entry["startAt"])
            entry_start = start_h * 60 + start_m
            duration_minutes = parse_duration(entry["duration"])
            entry_end = entry_start + duration_minutes

            if entry_start <= current_minutes < entry_end:
                remaining = entry_end - current_minutes
                end_h = entry_end // 60
                end_m = entry_end % 60
                ends_at = f"{end_h:02d}:{end_m:02d}"
                return ends_at, remaining

        return None, None

    def get_status(self) -> dict:
        if self.manual_override:
            if self.manual_override == "running":
                ends_at, remaining_minutes = self._calculate_remaining_time()
                return {
                    "filtering": True,
                    "manual_override": True,
                    "device_controlled": self.device is not None,
                    "device_running": self._device_running,
                    "started_at": self.last_action.isoformat() if self.last_action else None,
                    "started_by": self.action_by,
                    "ends_at": ends_at,
                    "remaining_minutes": remaining_minutes,
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
        self._scheduled_end_time = None
        
        if by == "scheduler" and self.schedule:
            now = datetime.now()
            current_minutes = now.hour * 60 + now.minute
            for entry in self.schedule:
                start_h, start_m = parse_time(entry["startAt"])
                entry_start = start_h * 60 + start_m
                duration_minutes = parse_duration(entry["duration"])
                entry_end = entry_start + duration_minutes
                
                if entry_start <= current_minutes < entry_end:
                    end_minutes = entry_end % (24 * 60)
                    end_dt = now.replace(
                        hour=end_minutes // 60,
                        minute=end_minutes % 60,
                        second=0,
                        microsecond=0
                    )
                    self._scheduled_end_time = end_dt
                    break
        
        if self.device:
            self._device_running = await self.device.start()
            return self._device_running
        return True

    async def stop_filtering(self, by: str = "manual") -> bool:
        self.manual_override = "stopped"
        self.last_action = datetime.now()
        self.action_by = by
        self._scheduled_end_time = None
        
        if self.device:
            self._device_running = not await self.device.stop()
            return not self._device_running
        return True

    def clear_override(self):
        self.manual_override = None
        self._scheduled_end_time = None


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
