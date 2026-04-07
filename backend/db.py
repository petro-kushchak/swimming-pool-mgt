import os
import json
from typing import Optional, List

POOLS_FILE = os.getenv("POOLS_CONFIG", "/data/pools.json")

_pools: List[dict] = []
_api_key: str = ""
_next_id: int = 1

def init_pools():
    global _pools, _api_key, _next_id
    if os.path.exists(POOLS_FILE):
        with open(POOLS_FILE, "r") as f:
            data = json.load(f)
            _pools = data.get("pools", [])
            _api_key = data.get("api_key", "")
    if _pools:
        _next_id = max(p["id"] for p in _pools) + 1

def get_api_key() -> str:
    return _api_key

def get_all_pools() -> List[dict]:
    return _pools

def get_pool_by_id(pool_id: int) -> Optional[dict]:
    for pool in _pools:
        if pool["id"] == pool_id:
            return pool
    return None

def create_pool(name: str, description: Optional[str], location: str, capacity: int, schedule: Optional[list]) -> dict:
    global _next_id
    pool = {
        "id": _next_id,
        "name": name,
        "description": description,
        "location": location,
        "capacity": capacity,
        "schedule": schedule
    }
    _pools.append(pool)
    _next_id += 1
    return pool
