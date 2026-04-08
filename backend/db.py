from __future__ import annotations

import json
import os
from typing import Optional

from config import settings, require_api_key
from schema import PoolsConfigSchema


class Database:
    _instance: Optional[Database] = None

    def __init__(self) -> None:
        self._pools: list[dict] = []
        self._api_key: str = ""
        self._next_id: int = 1

    @classmethod
    def get_instance(cls) -> Database:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def load(self) -> None:
        if os.path.exists(settings.pools_config):
            with open(settings.pools_config, "r") as f:
                data = json.load(f)
                validated = PoolsConfigSchema(**data)
                self._pools = [pool.model_dump() for pool in validated.pools]
        if self._pools:
            self._next_id = max(p["id"] for p in self._pools) + 1

    @property
    def api_key(self) -> str:
        return settings.api_key

    @property
    def pools(self) -> list[dict]:
        return self._pools

    def get_pool_by_id(self, pool_id: int) -> Optional[dict]:
        for pool in self._pools:
            if pool["id"] == pool_id:
                return pool
        return None

    def add_pool(
        self,
        name: str,
        description: Optional[str],
        location: str,
        capacity: int,
        schedule: Optional[list],
    ) -> dict:
        pool = {
            "id": self._next_id,
            "name": name,
            "description": description,
            "location": location,
            "capacity": capacity,
            "schedule": schedule,
        }
        self._pools.append(pool)
        self._next_id += 1
        return pool


_db = Database.get_instance()


def init_pools() -> None:
    require_api_key()
    _db.load()


def get_api_key() -> str:
    return _db.api_key


def get_all_pools() -> list[dict]:
    return _db.pools


def get_pool_by_id(pool_id: int) -> Optional[dict]:
    return _db.get_pool_by_id(pool_id)
