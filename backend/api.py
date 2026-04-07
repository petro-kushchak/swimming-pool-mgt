from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from db import init_pools, get_all_pools, get_pool_by_id, create_pool, get_api_key
from pool_status import init_pool_statuses, get_pool_status_by_id, get_all_pool_statuses, PoolStatus

app = FastAPI(
    title="Swimming Pool Management Service",
    description="A self-hosted service for managing swimming pools"
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, Optional[str]] = {}

    async def connect(self, websocket: WebSocket, api_key: Optional[str] = None):
        await websocket.accept()
        self.active_connections[websocket] = api_key

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    async def broadcast(self, message: dict, exclude_key: Optional[str] = None):
        for connection, key in self.active_connections.items():
            if key != exclude_key:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

async def verify_api_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    expected_key = get_api_key()
    if expected_key and api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

async def notify_all_clients():
    for pool_id, status in get_all_pool_statuses().items():
        await manager.broadcast({
            "pool_id": pool_id,
            "name": status.name,
            **status.get_status()
        })

@app.on_event("startup")
async def startup():
    init_pools()
    pools = get_all_pools()
    init_pool_statuses(pools)
    asyncio.create_task(broadcast_status_updates())

async def broadcast_status_updates():
    while True:
        for pool_id, status in get_all_pool_statuses().items():
            await manager.broadcast({
                "pool_id": pool_id,
                "name": status.name,
                **status.get_status()
            })
        await asyncio.sleep(30)

@app.websocket("/ws/status")
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
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/status/{pool_id}")
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
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

class ScheduleEntry(BaseModel):
    startAt: str
    duration: str

class Pool(BaseModel):
    name: str
    description: Optional[str] = None
    location: str
    capacity: int
    schedule: Optional[List[ScheduleEntry]] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to Swimming Pool Management Service"}

@app.get("/pools")
async def list_pools(request: Request):
    await verify_api_key(request)
    return get_all_pools()

@app.post("/pools")
async def add_pool(pool: Pool, request: Request):
    await verify_api_key(request)
    new_pool = create_pool(
        pool.name, pool.description, pool.location, pool.capacity, pool.schedule
    )
    init_pool_statuses(get_all_pools())
    return {"message": "Pool added successfully", "pool": new_pool}

@app.get("/pools/{pool_id}")
async def get_pool(pool_id: int, request: Request):
    await verify_api_key(request)
    result = get_pool_by_id(pool_id)
    if result:
        return result
    return {"error": "Pool not found"}

@app.get("/pools/{pool_id}/status")
async def get_pool_status_endpoint(pool_id: int, request: Request):
    await verify_api_key(request)
    status = get_pool_status_by_id(pool_id)
    if not status:
        return {"error": "Pool not found"}
    return {
        "pool_id": pool_id,
        "name": status.name,
        **status.get_status()
    }

@app.post("/pools/{pool_id}/start")
async def start_pool_filtering(pool_id: int, request: Request, by: str = "manual"):
    await verify_api_key(request)
    status = get_pool_status_by_id(pool_id)
    if not status:
        return {"error": "Pool not found"}
    status.start_filtering(by)
    response = {
        "pool_id": pool_id,
        "name": status.name,
        "message": "Filtering started",
        **status.get_status()
    }
    await manager.broadcast(response)
    return response

@app.post("/pools/{pool_id}/stop")
async def stop_pool_filtering(pool_id: int, request: Request, by: str = "manual"):
    await verify_api_key(request)
    status = get_pool_status_by_id(pool_id)
    if not status:
        return {"error": "Pool not found"}
    status.stop_filtering(by)
    response = {
        "pool_id": pool_id,
        "name": status.name,
        "message": "Filtering stopped",
        **status.get_status()
    }
    await manager.broadcast(response)
    return response

@app.post("/pools/{pool_id}/resume")
async def resume_pool_filtering(pool_id: int, request: Request):
    await verify_api_key(request)
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
