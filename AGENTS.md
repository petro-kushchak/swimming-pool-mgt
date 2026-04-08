# AGENTS.md - Swimming Pool Management Service

## Run Commands

```bash
# Run tests (requires Docker)
docker build -f backend/Dockerfile.test -t pool-mgt:test . && docker run --rm pool-mgt:test

# Build image (runs tests first unless --skip-tests)
./cicd/build.sh -v 0.2.0

# Run service
./cicd/run.sh -b    # build and run
./cicd/run.sh      # run existing image
```

## Architecture

- **Entry point**: `backend/main.py` → FastAPI app
- **API layer**: `backend/api.py` - REST routes + WebSocket
- **Business logic**: `backend/status.py`, `backend/scheduler.py`
- **Device control**: `backend/device.py` - HTTP calls to pool equipment
- **Config**: `pools.json` - defines pools, schedules, device URLs

## Testing

Tests live in `backend/tests/`. Use Docker to run (pytest installed from `backend/requirements.txt`). No local virtualenv required - everything runs in containers.

## Key Files

| File | Purpose |
|------|---------|
| `backend/api.py` | FastAPI routes, WebSocket handlers |
| `backend/pool_status.py` | Per-pool status, device on/off control |
| `backend/scheduler.py` | Automated filtering scheduler |
| `pools.json` | Pool config: schedules, device URLs |
| `VERSION` | Version file (read by build.sh) |

## Environment

- `POOLS_CONFIG`: config file path (default `/data/pools.json`)
- `SCHEDULER_INTERVAL`: seconds between scheduler checks (default 60)
- `API_PORT`: server port (default 8000)