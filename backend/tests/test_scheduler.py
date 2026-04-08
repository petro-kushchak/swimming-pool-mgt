import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, '/Users/pkushchak/Projects/home/swimming-pool-mgt/backend')

from scheduler import Scheduler
from utils import parse_time, parse_duration


class TestSchedulerHelpers:
    def test_parse_time(self):
        assert parse_time("06:00") == (6, 0)
        assert parse_time("23:59") == (23, 59)

    def test_parse_duration(self):
        assert parse_duration("3h") == 180
        assert parse_duration("30m") == 30
        assert parse_duration("2h 30m") == 150


class TestScheduler:
    def test_init_default_interval(self):
        scheduler = Scheduler()
        assert scheduler.interval == 60

    def test_init_custom_interval(self):
        scheduler = Scheduler(interval=30)
        assert scheduler.interval == 30

    def test_initial_state_not_running(self):
        scheduler = Scheduler()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_start(self):
        scheduler = Scheduler(interval=1)
        notify_mock = AsyncMock()
        
        await scheduler.start(notify_mock)
        
        assert scheduler._running is True
        assert scheduler._notify is not None
        
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop(self):
        scheduler = Scheduler()
        await scheduler.start(AsyncMock())
        await scheduler.stop()
        
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        scheduler = Scheduler()
        await scheduler.stop()
        assert scheduler._running is False
