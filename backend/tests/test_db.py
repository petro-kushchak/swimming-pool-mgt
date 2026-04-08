import pytest
import json
import tempfile
import os
from unittest import mock

import sys
sys.path.insert(0, '/Users/pkushchak/Projects/home/swimming-pool-mgt/backend')

from db import Database, init_pools, get_all_pools, get_pool_by_id


class TestDatabaseFunctions:
    def setup_method(self):
        Database.reset()

    def teardown_method(self):
        Database.reset()

    def test_init_pools_with_valid_config(self):
        config_data = {
            "api_key": "my-secret-key",
            "pools": [
                {"id": 1, "name": "Pool A", "location": "A", "capacity": 10},
                {"id": 2, "name": "Pool B", "location": "B", "capacity": 20},
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            temp_path = f.name
        
        try:
            with mock.patch("db.settings.pools_config", temp_path):
                with mock.patch("db.require_api_key", return_value="test-api-key"):
                    init_pools()
                    pools = get_all_pools()
                    
                    assert len(pools) == 2
                    assert pools[0]["name"] == "Pool A"
                    assert pools[1]["name"] == "Pool B"
        finally:
            os.unlink(temp_path)

    def test_init_pools_empty_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"pools": []}, f)
            f.flush()
            temp_path = f.name
        
        try:
            with mock.patch("db.settings.pools_config", temp_path):
                with mock.patch("db.require_api_key", return_value="test-api-key"):
                    init_pools()
                    pools = get_all_pools()
                    
                    assert pools == []
        finally:
            os.unlink(temp_path)

    def test_init_pools_invalid_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "pools": [
                    {"id": 1, "name": "Invalid Pool"}
                ],
            }, f)
            f.flush()
            temp_path = f.name
        
        try:
            with mock.patch("db.settings.pools_config", temp_path):
                with mock.patch("db.require_api_key", return_value="test-api-key"):
                    with pytest.raises(Exception):
                        init_pools()
        finally:
            os.unlink(temp_path)

    def test_get_pool_by_id_existing(self):
        config_data = {
            "api_key": "",
            "pools": [
                {"id": 1, "name": "Pool 1", "location": "A", "capacity": 10},
                {"id": 2, "name": "Pool 2", "location": "B", "capacity": 20},
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            temp_path = f.name
        
        try:
            with mock.patch("db.settings.pools_config", temp_path):
                with mock.patch("db.require_api_key", return_value="test-api-key"):
                    init_pools()
                    
                    pool = get_pool_by_id(1)
                    assert pool is not None
                    assert pool["name"] == "Pool 1"
                    
                    pool = get_pool_by_id(2)
                    assert pool is not None
                    assert pool["name"] == "Pool 2"
        finally:
            os.unlink(temp_path)

    def test_get_pool_by_id_not_found(self):
        config_data = {
            "api_key": "",
            "pools": [
                {"id": 1, "name": "Pool 1", "location": "A", "capacity": 10},
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            temp_path = f.name
        
        try:
            with mock.patch("db.settings.pools_config", temp_path):
                with mock.patch("db.require_api_key", return_value="test-api-key"):
                    init_pools()
                    
                    pool = get_pool_by_id(999)
                    assert pool is None
        finally:
            os.unlink(temp_path)

    def test_pools_with_schedule_parsed(self):
        config_data = {
            "api_key": "",
            "pools": [
                {
                    "id": 1,
                    "name": "Pool 1",
                    "location": "A",
                    "capacity": 10,
                    "schedule": [
                        {"startAt": "06:00", "duration": "3h"},
                        {"startAt": "14:00", "duration": "2h 30m"},
                    ],
                },
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            temp_path = f.name
        
        try:
            with mock.patch("db.settings.pools_config", temp_path):
                with mock.patch("db.require_api_key", return_value="test-api-key"):
                    init_pools()
                    
                    pool = get_pool_by_id(1)
                    assert pool is not None
                    assert len(pool["schedule"]) == 2
                    assert pool["schedule"][0]["startAt"] == "06:00"
                    assert pool["schedule"][1]["duration"] == "2h 30m"
        finally:
            os.unlink(temp_path)

    def test_pools_with_device_parsed(self):
        config_data = {
            "api_key": "",
            "pools": [
                {
                    "id": 1,
                    "name": "Pool 1",
                    "location": "A",
                    "capacity": 10,
                    "device": {
                        "name": "Filter Pump",
                        "start_url": "http://localhost/start",
                        "stop_url": "http://localhost/stop",
                        "status_url": "http://localhost/status",
                    },
                },
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            temp_path = f.name
        
        try:
            with mock.patch("db.settings.pools_config", temp_path):
                with mock.patch("db.require_api_key", return_value="test-api-key"):
                    init_pools()
                    
                    pool = get_pool_by_id(1)
                    assert pool is not None
                    assert pool["device"]["name"] == "Filter Pump"
                    assert pool["device"]["start_url"] == "http://localhost/start"
        finally:
            os.unlink(temp_path)
