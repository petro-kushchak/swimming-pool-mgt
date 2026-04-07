import pytest
import asyncio
from unittest.mock import AsyncMock, patch

import sys
sys.path.insert(0, '/Users/pkushchak/Projects/home/swimming-pool-mgt/backend')

from device import FilteringDevice, create_device


class TestFilteringDevice:
    def test_create_device_with_all_fields(self):
        config = {
            "name": "Test Pump",
            "start_url": "http://localhost/start",
            "stop_url": "http://localhost/stop",
            "status_url": "http://localhost/status"
        }
        device = create_device(config)
        
        assert device is not None
        assert device.name == "Test Pump"
        assert device.start_url == "http://localhost/start"
        assert device.stop_url == "http://localhost/stop"
        assert device.status_url == "http://localhost/status"

    def test_create_device_without_status_url(self):
        config = {
            "name": "Test Pump",
            "start_url": "http://localhost/start",
            "stop_url": "http://localhost/stop"
        }
        device = create_device(config)
        
        assert device is not None
        assert device.status_url is None

    def test_create_device_returns_none_for_empty_config(self):
        device = create_device(None)
        assert device is None

    @pytest.mark.asyncio
    async def test_start_success(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop"
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await device.start()
            assert result is True

    @pytest.mark.asyncio
    async def test_start_failure(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop"
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Connection failed"))
            
            result = await device.start()
            assert result is False

    @pytest.mark.asyncio
    async def test_stop_success(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop"
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await device.stop()
            assert result is True

    @pytest.mark.asyncio
    async def test_get_status_no_url(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop"
        )
        
        result = await device.get_status()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop",
            status_url="http://localhost/status"
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.text = "running"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await device.get_status()
            assert result == "running"
