import pytest
import json
import tempfile
import os

import sys
sys.path.insert(0, '/Users/pkushchak/Projects/home/swimming-pool-mgt/backend')

from schema import (
    PoolsConfigSchema,
    PoolSchema,
    ScheduleEntrySchema,
    DeviceSchema
)


class TestScheduleEntrySchema:
    def test_valid_schedule_entry(self):
        entry = ScheduleEntrySchema(startAt="06:00", duration="3h")
        assert entry.startAt == "06:00"
        assert entry.duration == "3h"

    def test_valid_schedule_entry_with_minutes(self):
        entry = ScheduleEntrySchema(startAt="12:30", duration="2h 30m")
        assert entry.startAt == "12:30"
        assert entry.duration == "2h 30m"

    def test_valid_schedule_entry_minutes_only(self):
        entry = ScheduleEntrySchema(startAt="09:00", duration="45m")
        assert entry.duration == "45m"

    def test_invalid_time_format(self):
        with pytest.raises(Exception):
            ScheduleEntrySchema(startAt="6:0", duration="1h")

    def test_invalid_duration_format(self):
        with pytest.raises(Exception):
            ScheduleEntrySchema(startAt="06:00", duration="1 hour")
    
    def test_duration_without_hours(self):
        entry = ScheduleEntrySchema(startAt="06:00", duration="30m")
        assert entry.duration == "30m"


class TestDeviceSchema:
    def test_valid_device(self):
        device = DeviceSchema(
            name="Test Pump",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop"
        )
        assert device.name == "Test Pump"
        assert device.status_url is None

    def test_valid_device_with_status_url(self):
        device = DeviceSchema(
            name="Test Pump",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop",
            status_url="http://localhost/status"
        )
        assert device.status_url == "http://localhost/status"

    def test_missing_required_field(self):
        with pytest.raises(Exception):
            DeviceSchema(name="Test", start_url="http://localhost/start")


class TestPoolSchema:
    def test_valid_pool(self):
        pool = PoolSchema(
            id=1,
            name="Test Pool",
            location="Building A",
            capacity=50
        )
        assert pool.id == 1
        assert pool.schedule is None
        assert pool.device is None

    def test_valid_pool_with_schedule(self):
        pool = PoolSchema(
            id=1,
            name="Test Pool",
            location="Building A",
            capacity=50,
            schedule=[
                ScheduleEntrySchema(startAt="06:00", duration="3h")
            ]
        )
        assert len(pool.schedule) == 1

    def test_valid_pool_with_device(self):
        pool = PoolSchema(
            id=1,
            name="Test Pool",
            location="Building A",
            capacity=50,
            device=DeviceSchema(
                name="Pump",
                start_url="http://localhost/start",
                stop_url="http://localhost/stop"
            )
        )
        assert pool.device is not None


class TestPoolsConfigSchema:
    def test_valid_config(self):
        config = PoolsConfigSchema(
            api_key="test-key",
            pools=[
                PoolSchema(id=1, name="Pool 1", location="A", capacity=10)
            ]
        )
        assert config.api_key == "test-key"
        assert len(config.pools) == 1

    def test_empty_api_key_allowed(self):
        config = PoolsConfigSchema(pools=[])
        assert config.api_key == ""

    def test_empty_pools_allowed(self):
        config = PoolsConfigSchema(pools=[])
        assert len(config.pools) == 0

    def test_invalid_pool_missing_required_field(self):
        with pytest.raises(Exception):
            PoolsConfigSchema(
                pools=[
                    PoolSchema(id=1, name="Pool")  # missing location
                ]
            )


class TestSchemaIntegration:
    def test_full_config_parsing(self):
        config_data = {
            "api_key": "secret-key",
            "pools": [
                {
                    "id": 1,
                    "name": "Olympic Pool",
                    "description": "Main pool",
                    "location": "Building A",
                    "capacity": 50,
                    "schedule": [
                        {"startAt": "06:00", "duration": "3h"},
                        {"startAt": "12:00", "duration": "2h 30m"}
                    ],
                    "device": {
                        "name": "Filter Pump",
                        "start_url": "http://pump/start",
                        "stop_url": "http://pump/stop"
                    }
                },
                {
                    "id": 2,
                    "name": "Kids Pool",
                    "location": "Building B",
                    "capacity": 20,
                    "schedule": [
                        {"startAt": "09:00", "duration": "4h"}
                    ]
                }
            ]
        }
        config = PoolsConfigSchema(**config_data)
        
        assert config.api_key == "secret-key"
        assert len(config.pools) == 2
        
        pool1 = config.pools[0]
        assert pool1.name == "Olympic Pool"
        assert len(pool1.schedule) == 2
        assert pool1.device.name == "Filter Pump"
        
        pool2 = config.pools[1]
        assert pool2.description is None
        assert pool2.device is None
