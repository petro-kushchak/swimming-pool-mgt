# swimming-pool-mgt
Self-hosted service for swimming pool management

## Setup

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   uvicorn main:app --reload
   ```

3. Open http://localhost:8000/docs for API documentation.

## Docker

Build and run with Docker:
```bash
docker build -t swimming-pool-mgt -f docker/Dockerfile .
docker run -p 8000:8000 swimming-pool-mgt
```

## API Endpoints

- GET / : Welcome message
- GET /pools : List all pools
- POST /pools : Add a new pool (JSON body: {"name": "string", "location": "string", "capacity": int})
- GET /pools/{pool_id} : Get a specific pool by ID
