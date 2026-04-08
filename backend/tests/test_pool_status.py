import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

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
        assert status._scheduled_end_time is None

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


class TestRemainingTimeCalculation:
    @pytest.fixture
    def schedule_3h(self):
        return [{"startAt": "10:00", "duration": "3h"}]

    @pytest.fixture
    def schedule_multiple(self):
        return [
            {"startAt": "06:00", "duration": "3h"},
            {"startAt": "12:00", "duration": "2h"},
            {"startAt": "18:00", "duration": "4h 30m"}
        ]

    @pytest.fixture
    def schedule_overnight(self):
        return [{"startAt": "22:00", "duration": "8h"}]

    def test_calculate_remaining_time_no_schedule(self):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=None)
        status.manual_override = "running"
        status.last_action = datetime.now()
        
        ends_at, remaining = status._calculate_remaining_time()
        
        assert ends_at is None
        assert remaining is None

    def test_calculate_remaining_time_no_last_action(self):
        schedule = [{"startAt": "06:00", "duration": "3h"}]
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule)
        status.manual_override = "running"
        
        ends_at, remaining = status._calculate_remaining_time()
        
        assert ends_at is None
        assert remaining is None

    def test_calculate_remaining_time_with_stored_end_time(self):
        schedule = [{"startAt": "10:00", "duration": "3h"}]
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule)
        status.manual_override = "running"
        status.last_action = datetime.now() - timedelta(hours=1)
        status._scheduled_end_time = datetime.now() + timedelta(hours=2)
        
        ends_at, remaining = status._calculate_remaining_time()
        
        assert ends_at is not None
        assert remaining is not None
        assert 115 <= remaining <= 125

    def test_calculate_remaining_time_expired(self):
        schedule = [{"startAt": "10:00", "duration": "3h"}]
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule)
        status.manual_override = "running"
        status.last_action = datetime.now() - timedelta(hours=4)
        status._scheduled_end_time = datetime.now() - timedelta(hours=1)
        
        ends_at, remaining = status._calculate_remaining_time()
        
        assert ends_at is None
        assert remaining == 0

    def test_calculate_remaining_time_within_current_schedule_window(self):
        schedule = [{"startAt": "06:00", "duration": "3h"}]
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule)
        status.manual_override = "running"
        status.last_action = datetime.now()
        status._scheduled_end_time = None
        
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        if 6 * 60 <= current_minutes < 9 * 60:
            ends_at, remaining = status._calculate_remaining_time()
            assert ends_at is not None
            assert remaining is not None
            assert remaining > 0
        else:
            pass

    @pytest.mark.asyncio
    async def test_start_filtering_by_scheduler_sets_end_time(self, schedule_3h):
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        if not (10 * 60 <= current_minutes < 13 * 60):
            pytest.skip("Test only valid when current time is within schedule window")
        
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule_3h)
        
        with patch('pool_status.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await status.start_filtering("scheduler")
        
        assert status._scheduled_end_time is not None
        assert status._scheduled_end_time > status.last_action

    @pytest.mark.asyncio
    async def test_start_filtering_by_manual_does_not_set_end_time(self, schedule_3h):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule_3h)
        
        await status.start_filtering("manual")
        
        assert status._scheduled_end_time is None

    @pytest.mark.asyncio
    async def test_stop_filtering_clears_end_time(self, schedule_3h):
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        if not (10 * 60 <= current_minutes < 13 * 60):
            pytest.skip("Test only valid when current time is within schedule window")
        
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule_3h)
        
        with patch('pool_status.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            await status.start_filtering("scheduler")
        
        assert status._scheduled_end_time is not None
        
        await status.stop_filtering("manual")
        assert status._scheduled_end_time is None

    def test_clear_override_clears_end_time(self, schedule_3h):
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule_3h)
        status.manual_override = "running"
        status._scheduled_end_time = datetime.now() + timedelta(hours=2)
        
        status.clear_override()
        
        assert status._scheduled_end_time is None

    def test_get_status_remaining_time_in_schedule_window(self):
        schedule = [{"startAt": "10:00", "duration": "3h"}]
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule)
        
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        if 10 * 60 <= current_minutes < 13 * 60:
            with patch('pool_status.datetime') as mock_datetime:
                mock_datetime.now.return_value = now
                mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
                
                status.manual_override = "running"
                status.last_action = now
                status._scheduled_end_time = now + timedelta(hours=2)
                
                result = status.get_status()
                
                assert result["ends_at"] is not None
                assert result["remaining_minutes"] is not None
                assert result["remaining_minutes"] > 0
                assert result["remaining_minutes"] <= 125

    def test_get_status_no_remaining_time_outside_schedule(self):
        schedule = [{"startAt": "06:00", "duration": "2h"}]
        status = PoolStatus(pool_id=1, name="Test Pool", schedule=schedule)
        
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        if not (6 * 60 <= current_minutes < 8 * 60):
            status.manual_override = "running"
            status.last_action = now - timedelta(hours=5)
            status._scheduled_end_time = None
            
            result = status.get_status()
            
            assert result["ends_at"] is None
            assert result["remaining_minutes"] is None

    def test_remaining_time_format(self):
        schedule = [{"startAt": "08:00", "duration": "13h"}]
        status = PoolStatus(pool_id=1, name="Jacuzzi", schedule=schedule)
        
        now = datetime.now()
        with patch('pool_status.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            status.manual_override = "running"
            status.last_action = now
            status._scheduled_end_time = now + timedelta(hours=7, minutes=30)
            
            result = status.get_status()
            
            assert result["ends_at"] is not None
            assert ":" in result["ends_at"]
            hours, mins = result["ends_at"].split(":")
            assert int(hours) >= 0 and int(hours) <= 23
            assert int(mins) >= 0 and int(mins) <= 59
