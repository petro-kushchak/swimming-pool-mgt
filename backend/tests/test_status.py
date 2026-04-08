import pytest
import sys
sys.path.insert(0, '/Users/pkushchak/Projects/home/swimming-pool-mgt/backend')

from status import get_pool_status
from utils import parse_time, parse_duration


class TestParseTime:
    def test_parse_valid_time(self):
        assert parse_time("06:00") == (6, 0)
        assert parse_time("23:59") == (23, 59)
        assert parse_time("00:00") == (0, 0)
        assert parse_time("12:30") == (12, 30)

    def test_parse_time_single_digit(self):
        assert parse_time("6:00") == (6, 0)
        assert parse_time("9:5") == (9, 5)


class TestParseDuration:
    def test_parse_hours_only(self):
        assert parse_duration("3h") == 180
        assert parse_duration("1h") == 60
        assert parse_duration("24h") == 1440

    def test_parse_minutes_only(self):
        assert parse_duration("30m") == 30
        assert parse_duration("15m") == 15

    def test_parse_hours_and_minutes(self):
        assert parse_duration("2h 30m") == 150
        assert parse_duration("1h 15m") == 75
        assert parse_duration("3h 45m") == 225

    def test_parse_duration_invalid_returns_default(self):
        assert parse_duration("invalid") == 60
        assert parse_duration("") == 60


class TestGetPoolStatus:
    def test_no_schedule(self):
        result = get_pool_status(None)
        assert result["filtering"] is False
        assert result["next_filter"] is None

    def test_empty_schedule(self):
        result = get_pool_status([])
        assert result["filtering"] is False

    def test_schedule_with_valid_entries(self):
        schedule = [
            {"startAt": "06:00", "duration": "3h"},
            {"startAt": "12:00", "duration": "2h"}
        ]
        result = get_pool_status(schedule)
        
        assert "filtering" in result
        assert "next_filter" in result
        assert "last_filtered" in result

    def test_schedule_structure(self):
        schedule = [{"startAt": "06:00", "duration": "3h"}]
        result = get_pool_status(schedule)
        
        assert isinstance(result["filtering"], bool)
