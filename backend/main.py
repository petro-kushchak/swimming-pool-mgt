import uvicorn

from api import app
from config import config
from db import init_pools, get_all_pools
from pool_status import init_pool_statuses
from scheduler import scheduler
from api import manager


async def start_scheduler():
    async def notify(pool_id, status):
        await manager.broadcast({
            "pool_id": pool_id,
            "name": status.name,
            "message": f"Scheduler {'started' if status.manual_override == 'running' else 'stopped'} filtering",
            **status.get_status()
        })
    await scheduler.start(notify)


@app.on_event("startup")
async def startup():
    init_pools()
    init_pool_statuses(get_all_pools())
    await start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    await scheduler.stop()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.api_port)
