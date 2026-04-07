import os
import asyncio
import re
from datetime import datetime
from typing import Optional
from pool_status import get_pool_status_by_id, get_all_pool_statuses, PoolStatus

SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", "60"))

def parse_time(time_str: str) -> tuple[int, int]:
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])

def parse_duration(duration_str: str) -> int:
    total_minutes = 0
    hours_match = re.search(r'(\d+)h', duration_str)
    minutes_match = re.search(r'(\d+)m', duration_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60
    if minutes_match:
        total_minutes += int(minutes_match.group(1))
    return total_minutes if total_minutes > 0 else 60

class Scheduler:
    def __init__(self, interval: int = None):
        self.interval = interval or SCHEDULER_INTERVAL
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, notify_callback):
        self._running = True
        self._notify = notify_callback
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self):
        while self._running:
            await self._check_pools()
            await asyncio.sleep(self.interval)

    async def _check_pools(self):
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute

        for pool_id, status in get_all_pool_statuses().items():
            if status.manual_override:
                continue

            if not status.schedule:
                continue

            should_filter = False
            for entry in status.schedule:
                start_h, start_m = parse_time(entry["startAt"])
                start_minutes = start_h * 60 + start_m
                duration_minutes = parse_duration(entry["duration"])
                end_minutes = start_minutes + duration_minutes

                if start_minutes <= current_minutes < end_minutes:
                    should_filter = True
                    break

            if should_filter and status.manual_override != "running":
                await status.start_filtering("scheduler")
                await self._notify(pool_id, status)
            elif not should_filter and status.manual_override == "running":
                await status.stop_filtering("scheduler")
                await self._notify(pool_id, status)

scheduler = Scheduler()
