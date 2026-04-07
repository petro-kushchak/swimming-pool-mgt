from datetime import datetime
from typing import Optional
from status import get_pool_status

class PoolStatus:
    def __init__(self, pool_id: int, name: str, schedule: list):
        self.pool_id = pool_id
        self.name = name
        self.schedule = schedule
        self.manual_override: Optional[str] = None
        self.last_action: Optional[datetime] = None
        self.action_by: Optional[str] = None

    def get_status(self) -> dict:
        if self.manual_override:
            if self.manual_override == "running":
                return {
                    "filtering": True,
                    "manual_override": True,
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
                    "stopped_at": self.last_action.isoformat() if self.last_action else None,
                    "stopped_by": self.action_by,
                    "next_filter": None,
                    "last_filtered": self.last_action.strftime("%H:%M") if self.last_action else None
                }
        
        return get_pool_status(self.schedule)

    def start_filtering(self, by: str = "manual"):
        self.manual_override = "running"
        self.last_action = datetime.now()
        self.action_by = by

    def stop_filtering(self, by: str = "manual"):
        self.manual_override = "stopped"
        self.last_action = datetime.now()
        self.action_by = by

    def clear_override(self):
        self.manual_override = None


_pool_statuses: dict[int, PoolStatus] = {}

def init_pool_statuses(pools: list):
    _pool_statuses.clear()
    for pool in pools:
        status = PoolStatus(pool["id"], pool["name"], pool.get("schedule"))
        _pool_statuses[pool["id"]] = status

def get_pool_status_by_id(pool_id: int) -> Optional[PoolStatus]:
    return _pool_statuses.get(pool_id)

def get_all_pool_statuses() -> dict[int, PoolStatus]:
    return _pool_statuses
