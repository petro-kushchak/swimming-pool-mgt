import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, '/Users/pkushchak/Projects/home/swimming-pool-mgt/backend')

from pool_status import PoolStatus


class TestPoolStatus:
    def test_init(self):
        schedule = [{"startAt": "06:00", "duration": "3h"}]
        status = PoolStatus(
            pool_id=1,
            name="Test Pool",
            schedule=schedule
        )
        
        assert status.pool_id == 1
        assert status.name == "Test Pool"
        assert status.schedule == schedule
        assert status.manual_override is None
        assert status.last_action is None

    def test_init_without_schedule(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        
        assert status.schedule is None
        assert status.manual_override is None

    def test_init_with_device(self):
        device = MagicMock()
        device.name = "Test Device"
        
        status = PoolStatus(
            pool_id=1,
            name="Test Pool",
            schedule=None,
            device=device
        )
        
        assert status.device is not None
        assert status.device.name == "Test Device"

    def test_get_status_no_override_no_schedule(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        result = status.get_status()
        
        assert result["filtering"] is False
        assert "manual_override" not in result or result.get("manual_override") is not True

    def test_get_status_running_override(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        status.manual_override = "running"
        status.last_action = datetime.now()
        status.action_by = "test"
        
        result = status.get_status()
        
        assert result["filtering"] is True
        assert result["manual_override"] is True
        assert result["started_by"] == "test"
        assert result["started_at"] is not None

    def test_get_status_stopped_override(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        status.manual_override = "stopped"
        status.last_action = datetime.now()
        status.action_by = "test"
        
        result = status.get_status()
        
        assert result["filtering"] is False
        assert result["manual_override"] is True
        assert result["stopped_by"] == "test"

    def test_clear_override(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        status.manual_override = "running"
        
        status.clear_override()
        
        assert status.manual_override is None

    @pytest.mark.asyncio
    async def test_start_filtering_without_device(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        
        result = await status.start_filtering("test")
        
        assert result is True
        assert status.manual_override == "running"
        assert status.action_by == "test"

    @pytest.mark.asyncio
    async def test_start_filtering_with_device_success(self):
        device = AsyncMock()
        device.start = AsyncMock(return_value=True)
        
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None, device=device)
        
        result = await status.start_filtering("test")
        
        assert result is True
        assert status._device_running is True
        device.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_filtering_with_device_failure(self):
        device = AsyncMock()
        device.start = AsyncMock(return_value=False)
        
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None, device=device)
        
        result = await status.start_filtering("test")
        
        assert result is False
        assert status._device_running is False

    @pytest.mark.asyncio
    async def test_stop_filtering_without_device(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        
        result = await status.stop_filtering("test")
        
        assert result is True
        assert status.manual_override == "stopped"
        assert status.action_by == "test"

    @pytest.mark.asyncio
    async def test_stop_filtering_with_device_success(self):
        device = AsyncMock()
        device.stop = AsyncMock(return_value=True)
        
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None, device=device)
        
        result = await status.stop_filtering("test")
        
        assert result is True
        assert status._device_running is False
        device.stop.assert_called_once()
