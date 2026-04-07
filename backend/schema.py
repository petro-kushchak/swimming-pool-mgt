from pydantic import BaseModel, Field
from typing import Optional, List


class DeviceSchema(BaseModel):
    name: str
    start_url: str
    stop_url: str
    status_url: Optional[str] = None


class ScheduleEntrySchema(BaseModel):
    startAt: str = Field(pattern=r"^\d{1,2}:\d{2}$")
    duration: str = Field(pattern=r"^(\d+h)?\s*(\d+m)?$")


class PoolSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    location: str
    capacity: int
    schedule: Optional[List[ScheduleEntrySchema]] = None
    device: Optional[DeviceSchema] = None


class PoolsConfigSchema(BaseModel):
    api_key: Optional[str] = ""
    pools: List[PoolSchema]
