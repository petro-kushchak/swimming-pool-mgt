from __future__ import annotations

import re
from typing import Tuple

DEFAULT_DURATION_MINUTES = 60


def parse_time(time_str: str) -> Tuple[int, int]:
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


def parse_duration(duration_str: str) -> int:
    total_minutes = 0
    hours_match = re.search(r"(\d+)h", duration_str)
    minutes_match = re.search(r"(\d+)m", duration_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60
    if minutes_match:
        total_minutes += int(minutes_match.group(1))
    return total_minutes if total_minutes > 0 else DEFAULT_DURATION_MINUTES
