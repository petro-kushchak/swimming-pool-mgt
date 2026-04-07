from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel
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

class ScheduleEntry(BaseModel):
    startAt: str
    duration: str

class Pool(BaseModel):
    name: str
    description: Optional[str] = None
    location: str
    capacity: int
    schedule: Optional[List[ScheduleEntry]] = None

@api_router.get("/version")
def read_version():
    return {"version": get_version()}

@api_router.get("/pools")
async def list_pools(request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    return get_all_pools()

@api_router.get("/pools/{pool_id}")
async def get_pool(pool_id: int, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    result = get_pool_by_id(pool_id)
    if result:
        return result
    return {"error": "Pool not found"}

@api_router.get("/pools/{pool_id}/status")
async def get_pool_status_endpoint(pool_id: int, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return {"error": "Pool not found"}
    return {
        "pool_id": pool_id,
        "name": status.name,
        **status.get_status()
    }

@api_router.put("/pools/{pool_id}/start")
async def start_pool_filtering(pool_id: int, request: Request, by: str = "manual"):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return {"error": "Pool not found"}
    success = await status.start_filtering(by)
    response = {
        "pool_id": pool_id,
        "name": status.name,
        "message": "Filtering started",
        "device_triggered": success if status.device else None,
        **status.get_status()
    }
    await manager.broadcast(response)
    return response

@api_router.put("/pools/{pool_id}/stop")
async def stop_pool_filtering(pool_id: int, request: Request, by: str = "manual"):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return {"error": "Pool not found"}
    success = await status.stop_filtering(by)
    response = {
        "pool_id": pool_id,
        "name": status.name,
        "message": "Filtering stopped",
        "device_triggered": success if status.device else None,
        **status.get_status()
    }
    await manager.broadcast(response)
    return response

@api_router.put("/pools/{pool_id}/resume")
async def resume_pool_filtering(pool_id: int, request: Request):
    verify_api_key(request.headers.get("X-API-Key"))
    status = get_pool_status_by_id(pool_id)
    if not status:
        return {"error": "Pool not found"}
    status.clear_override()
    response = {
        "pool_id": pool_id,
        "name": status.name,
        "message": "Manual override cleared, schedule resumed",
        **status.get_status()
    }
    await manager.broadcast(response)
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
    
    @app.get("/")
    def read_root():
        return {
            "service": "Swimming Pool Management Service",
            "version": version,
            "docs": "/docs"
        }
    
    return app

app = create_app()
