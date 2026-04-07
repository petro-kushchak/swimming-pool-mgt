from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Swimming Pool Management Service", description="A self-hosted service for managing swimming pools")

class Pool(BaseModel):
    name: str
    location: str
    capacity: int

pools = []

@app.get("/")
def read_root():
    return {"message": "Welcome to Swimming Pool Management Service"}

@app.get("/pools")
def get_pools():
    return pools

@app.post("/pools")
def add_pool(pool: Pool):
    pools.append(pool.dict())
    return {"message": "Pool added successfully"}

@app.get("/pools/{pool_id}")
def get_pool(pool_id: int):
    if 0 <= pool_id < len(pools):
        return pools[pool_id]
    return {"error": "Pool not found"}