import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

def parse_time(time_str: str) -> Tuple[int, int]:
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])

def parse_duration(duration_str: str) -> int:
    total_minutes = 0
    hours = re.search(r'(\d+)h', duration_str)
    minutes = re.search(r'(\d+)m', duration_str)
    if hours:
        total_minutes += int(hours.group(1)) * 60
    if minutes:
        total_minutes += int(minutes.group(1))
    return total_minutes

def get_pool_status(schedule: list) -> dict:
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    today = now.weekday()
    
    if not schedule:
        return {"filtering": False, "next_filter": None, "last_filtered": None}
    
    sorted_schedule = sorted(schedule, key=lambda x: parse_time(x["startAt"])[0] * 60 + parse_time(x["startAt"])[1])
    
    last_filter = None
    is_filtering = False
    
    for entry in sorted_schedule:
        start_h, start_m = parse_time(entry["startAt"])
        start_minutes = start_h * 60 + start_m
        duration_minutes = parse_duration(entry["duration"])
        end_minutes = start_minutes + duration_minutes
        
        if start_minutes <= current_minutes < end_minutes:
            is_filtering = True
            remaining = end_minutes - current_minutes
            return {
                "filtering": True,
                "ends_at": f"{(start_h + (start_m + duration_minutes) // 60) % 24}:{(start_m + duration_minutes) % 60:02d}",
                "remaining_minutes": remaining,
                "next_filter": None,
                "last_filtered": None
            }
        
        if current_minutes >= end_minutes:
            last_filter = entry
    
    next_entry = None
    for entry in sorted_schedule:
        start_h, start_m = parse_time(entry["startAt"])
        start_minutes = start_h * 60 + start_m
        if start_minutes > current_minutes:
            next_entry = entry
            break
    
    if next_entry is None and sorted_schedule:
        next_entry = sorted_schedule[0]
    
    next_filter = None
    if next_entry:
        next_filter = next_entry["startAt"]
    
    last_filtered = None
    if last_filter:
        start_h, start_m = parse_time(last_filter["startAt"])
        duration_minutes = parse_duration(last_filter["duration"])
        filtered_end = start_h * 60 + start_m + duration_minutes
        last_filtered = f"{(filtered_end // 60) % 24}:{filtered_end % 60:02d}"
    
    return {
        "filtering": False,
        "next_filter": next_filter,
        "last_filtered": last_filtered
    }
