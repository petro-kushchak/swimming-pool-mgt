from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List

from db import get_all_pools, get_pool_by_id, get_api_key
from pool_status import get_pool_status_by_id, get_all_pool_statuses, PoolStatus
from version import get_version

api_router = APIRouter(prefix="/api/v1")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, Optional[str]] = {}

    async def connect(self, websocket: WebSocket, api_key: Optional[str] = None):
        await websocket.accept()
        self.active_connections[websocket] = api_key

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections.keys()):
            try:
                await connection.send_json(message)
            except:
                self.active_connections.pop(connection, None)


manager = ConnectionManager()


class ScheduleEntry(BaseModel):
    startAt: str = Field(description="Start time in HH:MM format")
    duration: str = Field(description="Duration like '3h' or '2h 30m'")


class Device(BaseModel):
    name: str = Field(description="Device name")
    start_url: str = Field(description="HTTP URL to start the device")
    stop_url: str = Field(description="HTTP URL to stop the device")
    status_url: Optional[str] = Field(default=None, description="HTTP URL to check device status")


class Pool(BaseModel):
    id: int = Field(description="Unique pool identifier")
    name: str = Field(description="Pool name")
    description: Optional[str] = Field(default=None, description="Pool description")
    location: str = Field(description="Pool location")
    capacity: int = Field(description="Pool capacity")
    schedule: Optional[List[ScheduleEntry]] = Field(default=None, description="Filtering schedule")
    device: Optional[Device] = Field(default=None, description="Filtering device configuration")


class PoolStatus(BaseModel):
    pool_id: int = Field(description="Pool identifier")
    name: str = Field(description="Pool name")
    filtering: bool = Field(description="Whether the pool is currently filtering")
    manual_override: Optional[bool] = Field(default=None, description="Whether manual control is active")
    device_controlled: Optional[bool] = Field(default=None, description="Whether device is configured")
    device_running: Optional[bool] = Field(default=None, description="Device running state")
    ends_at: Optional[str] = Field(default=None, description="When current filtering ends (HH:MM)")
    remaining_minutes: Optional[int] = Field(default=None, description="Minutes until filtering ends")
    next_filter: Optional[str] = Field(default=None, description="Next scheduled filter start (HH:MM)")
    last_filtered: Optional[str] = Field(default=None, description="Last filtering ended at (HH:MM)")
    started_at: Optional[str] = Field(default=None, description="Manual start timestamp")
    started_by: Optional[str] = Field(default=None, description="Who triggered start")
    stopped_at: Optional[str] = Field(default=None, description="Manual stop timestamp")
    stopped_by: Optional[str] = Field(default=None, description="Who triggered stop")


class PoolActionResponse(BaseModel):
    pool_id: int = Field(description="Pool identifier")
    name: str = Field(description="Pool name")
    message: str = Field(description="Action message")
    device_triggered: Optional[bool] = Field(default=None, description="Device HTTP call result")
    filtering: bool = Field(description="Current filtering state")
    manual_override: Optional[bool] = Field(default=None, description="Manual override state")
    device_controlled: Optional[bool] = Field(default=None, description="Device controlled")
    device_running: Optional[bool] = Field(default=None, description="Device running")
    ends_at: Optional[str] = Field(default=None, description="When filtering ends")
    remaining_minutes: Optional[int] = Field(default=None, description="Remaining minutes")
    next_filter: Optional[str] = Field(default=None, description="Next filter time")
    last_filtered: Optional[str] = Field(default=None, description="Last filtered time")
    started_at: Optional[str] = Field(default=None, description="Start timestamp")
    started_by: Optional[str] = Field(default=None, description="Started by")
    stopped_at: Optional[str] = Field(default=None, description="Stop timestamp")
    stopped_by: Optional[str] = Field(default=None, description="Stopped by")


class ErrorResponse(BaseModel):
    error: str = Field(description="Error message")


class VersionResponse(BaseModel):
    version: str = Field(description="Service version")


class ServiceInfo(BaseModel):
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    docs: str = Field(description="Documentation URL")


@api_router.websocket("/ws/status")
async def websocket_status(websocket: WebSocket, api_key: Optional[str] = None):
    expected_key = get_api_key()
    if expected_key and api_key != expected_key:
        await websocket.close(code=4001)
        return
    await manager.connect(websocket, api_key)
    try:
        while True:
            for pool_id, status in get_all_pool_statuses().items():
                await websocket.send_json({
                    "pool_id": pool_id,
                    "name": status.name,
                    **status.get_status()
                })
            import asyncio
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@api_router.websocket("/ws/status/{pool_id}")
async def websocket_pool_status(websocket: WebSocket, pool_id: int, api_key: Optional[str] = None):
    expected_key = get_api_key()
    if expected_key and api_key != expected_key:
        await websocket.close(code=4001)
        return
    await manager.connect(websocket, api_key)
    try:
        while True:
            status = get_pool_status_by_id(pool_id)
            if status:
                await websocket.send_json({
                    "pool_id": pool_id,
                    "name": status.name,
                    **status.get_status()
                })
            else:
                await websocket.send_json({"error": "Pool not found"})
                break
            import asyncio
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def verify_api_key(api_key: Optional[str]) -> Optional[str]:
    expected_key = get_api_key()
    if expected_key and api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@api_router.get(
    "/version",
    response_model=VersionResponse,
    summary="Get service version"
)
def read_version():
    return VersionResponse(version=get_version())


@api_router.get(
    "/pools",
    response_model=List[Pool],
    summary="List all pools"
)
async def list_pools(request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    return get_all_pools()


@api_router.get(
    "/pools/{pool_id}",
    response_model=Pool,
    responses={404: {"model": ErrorResponse}},
    summary="Get pool by ID"
)
async def get_pool(pool_id: int, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    result = get_pool_by_id(pool_id)
    if result:
        return result
    return ErrorResponse(error="Pool not found")


@api_router.get(
    "/pools/{pool_id}/status",
    response_model=PoolStatus,
    responses={404: {"model": ErrorResponse}},
    summary="Get pool filtering status"
)
async def get_pool_status_endpoint(pool_id: int, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return ErrorResponse(error="Pool not found")
    status_data = status.get_status()
    return PoolStatus(pool_id=pool_id, name=status.name, **status_data)


@api_router.put(
    "/pools/{pool_id}/start",
    response_model=PoolActionResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Start pool filtering"
)
async def start_pool_filtering(pool_id: int, request: Request, by: str = "manual"):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return ErrorResponse(error="Pool not found")
    success = await status.start_filtering(by)
    status_data = status.get_status()
    response = PoolActionResponse(
        pool_id=pool_id,
        name=status.name,
        message="Filtering started",
        device_triggered=success if status.device else None,
        **status_data
    )
    await manager.broadcast({
        "pool_id": pool_id,
        "name": status.name,
        "message": "Filtering started",
        **status_data
    })
    return response


@api_router.put(
    "/pools/{pool_id}/stop",
    response_model=PoolActionResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Stop pool filtering"
)
async def stop_pool_filtering(pool_id: int, request: Request, by: str = "manual"):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return ErrorResponse(error="Pool not found")
    success = await status.stop_filtering(by)
    status_data = status.get_status()
    response = PoolActionResponse(
        pool_id=pool_id,
        name=status.name,
        message="Filtering stopped",
        device_triggered=success if status.device else None,
        **status_data
    )
    await manager.broadcast({
        "pool_id": pool_id,
        "name": status.name,
        "message": "Filtering stopped",
        **status_data
    })
    return response


@api_router.put(
    "/pools/{pool_id}/resume",
    response_model=PoolActionResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Resume scheduled filtering"
)
async def resume_pool_filtering(pool_id: int, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return ErrorResponse(error="Pool not found")
    status.clear_override()
    status_data = status.get_status()
    response = PoolActionResponse(
        pool_id=pool_id,
        name=status.name,
        message="Manual override cleared, schedule resumed",
        **status_data
    )
    await manager.broadcast({
        "pool_id": pool_id,
        "name": status.name,
        "message": "Manual override cleared, schedule resumed",
        **status_data
    })
    return response


def create_app() -> FastAPI:
    version = get_version()
    app = FastAPI(
        title="Swimming Pool Management Service",
        description="A self-hosted service for managing swimming pools",
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    app.include_router(api_router)
    
    # @app.get("/", response_model=ServiceInfo)
    # def read_root():
    #     return ServiceInfo(
    #         service="Swimming Pool Management Service",
    #         version=version,
    #         docs="/docs"
    #     )
    
    return app


app = create_app()
