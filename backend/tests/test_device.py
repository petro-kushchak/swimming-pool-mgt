import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import sys
sys.path.insert(0, '/Users/pkushchak/Projects/home/swimming-pool-mgt/backend')

from device import FilteringDevice, create_device


@pytest.fixture(autouse=True)
async def reset_client():
    FilteringDevice._client = None
    yield
    FilteringDevice._client = None


class TestFilteringDevice:
    def test_create_device_with_all_fields(self):
        config = {
            "name": "Test Pump",
            "start_url": "http://localhost/start",
            "stop_url": "http://localhost/stop",
            "status_url": "http://localhost/status",
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
            "stop_url": "http://localhost/stop",
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
            stop_url="http://localhost/stop",
        )
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        with patch.object(FilteringDevice, 'get_client', new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            result = await device.start()
            assert result is True

    @pytest.mark.asyncio
    async def test_start_failure(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop",
        )
        
        with patch.object(FilteringDevice, 'get_client', new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            import httpx
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_get_client.return_value = mock_client
            
            result = await device.start()
            assert result is False

    @pytest.mark.asyncio
    async def test_stop_success(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop",
        )
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        with patch.object(FilteringDevice, 'get_client', new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            result = await device.stop()
            assert result is True

    @pytest.mark.asyncio
    async def test_get_status_no_url(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop",
        )
        
        result = await device.get_status()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        device = FilteringDevice(
            name="Test",
            start_url="http://localhost/start",
            stop_url="http://localhost/stop",
            status_url="http://localhost/status",
        )
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "running"
        
        with patch.object(FilteringDevice, 'get_client', new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            result = await device.get_status()
            assert result == "running"
