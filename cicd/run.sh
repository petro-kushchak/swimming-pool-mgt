#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_DIR/VERSION"
API_KEY_FILE="$PROJECT_DIR/.api_key"

usage() {
    echo "Usage: $0 [-v VERSION] [-d POOLS_CONFIG] [-i INTERVAL] [-p PORT] [-P UI_PORT] [-k API_KEY] [-b] [-r] [--stop] [--logs] [--api-only] [--ui-only]"
    echo ""
    echo "Options:"
    echo "  -v VERSION       Version to build/run (default: from VERSION file)"
    echo "  -d POOLS_CONFIG  Path to pools.json (default: ./pools.json)"
    echo "  -i INTERVAL      Scheduler interval in seconds (default: 60)"
    echo "  -p PORT          API port to expose (default: 8082)"
    echo "  -P UI_PORT       UI port to expose (default: 8080)"
    echo "  -k API_KEY       API key for authentication (auto-generated if not provided)"
    echo "  -b               Build images before running"
    echo "  -r               Remove existing containers before running"
    echo "  --stop           Stop and remove running containers"
    echo "  --logs           Show container logs"
    echo "  --api-only       Run only API service"
    echo "  --ui-only        Run only UI service"
    echo ""
    echo "Note: API key is persisted to .api_key file for consistency across runs."
    exit 1
}

VERSION=""
STOP=false
BUILD=false
REMOVE=false
SHOW_LOGS=false
PORT=8082
UI_PORT=8080
POOLS_CONFIG="./pools.json"
INTERVAL=60
API_KEY=""
RUN_API=true
RUN_UI=true

for arg in "$@"; do
    case "$arg" in
        --stop) STOP=true ;;
        --logs) SHOW_LOGS=true ;;
        --api-only) RUN_UI=false ;;
        --ui-only) RUN_API=false ;;
    esac
done

if [ "$STOP" = true ]; then
    echo "Stopping services..."
    cd "$PROJECT_DIR" && docker compose down
    echo "Done."
    exit 0
fi

if [ "$SHOW_LOGS" = true ]; then
    echo "Showing logs..."
    cd "$PROJECT_DIR" && docker compose logs -f
    exit 0
fi

while getopts "v:d:i:p:P:k:brh" opt; do
    case $opt in
        v) VERSION="$OPTARG" ;;
        d) POOLS_CONFIG="$OPTARG" ;;
        i) INTERVAL="$OPTARG" ;;
        p) PORT="$OPTARG" ;;
        P) UI_PORT="$OPTARG" ;;
        k) API_KEY="$OPTARG" ;;
        b) BUILD=true ;;
        r) REMOVE=true ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [ -z "$VERSION" ] && [ -f "$VERSION_FILE" ]; then
    VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
fi

if [ "$REMOVE" = true ]; then
    echo "Removing existing containers..."
    cd "$PROJECT_DIR" && docker compose down 2>/dev/null || true
fi

if [ -z "$API_KEY" ]; then
    if [ -f "$API_KEY_FILE" ]; then
        API_KEY=$(cat "$API_KEY_FILE")
        echo "Using existing API key from .api_key file"
    else
        API_KEY=$(openssl rand -hex 32)
        echo "$API_KEY" > "$API_KEY_FILE"
        chmod 600 "$API_KEY_FILE"
        echo "Generated new API key and saved to .api_key file"
    fi
else
    echo "$API_KEY" > "$API_KEY_FILE"
    chmod 600 "$API_KEY_FILE"
fi

if [ "$BUILD" = true ]; then
    if [ -z "$VERSION" ]; then
        echo "Error: Version required for build"
        exit 1
    fi
    
    build_args="--skip-tests"
    if [ "$RUN_API" = true ] && [ "$RUN_UI" = true ]; then
        :
    elif [ "$RUN_API" = true ]; then
        build_args="$build_args --api-only"
    else
        build_args="$build_args --ui-only"
    fi
    
    echo "Building images ${VERSION}..."
    cd "$PROJECT_DIR" && ./cicd/build.sh -v "$VERSION" $build_args
fi

cd "$PROJECT_DIR"

POOLS_CONFIG_ABS=$(realpath "$POOLS_CONFIG" 2>/dev/null || echo "$POOLS_CONFIG")

echo ""
echo "Starting Swimming Pool Management Service..."
echo "  Version: ${VERSION:-latest}"
echo "  API Port: $PORT"
echo "  UI Port: $UI_PORT"
echo "  Pools config: $POOLS_CONFIG_ABS"
echo "  Scheduler interval: ${INTERVAL}s"
echo ""

export BUILD_VERSION="${VERSION:-unknown}"
export API_PORT="$PORT"
export UI_PORT="$UI_PORT"
export UI_API_URL="http://localhost:$PORT"
export UI_WS_URL="ws://localhost:$PORT"
export POOLS_CONFIG="$POOLS_CONFIG_ABS"
export SCHEDULER_INTERVAL="$INTERVAL"
export API_KEY="$API_KEY"
export COMPOSE_PROJECT_NAME="pool-mgt"

if [ "$RUN_API" = true ] && [ "$RUN_UI" = true ]; then
    API_KEY="$API_KEY" docker compose up -d
elif [ "$RUN_API" = true ]; then
    API_KEY="$API_KEY" docker compose up -d pool-mgt-api
else
    API_KEY="$API_KEY" docker compose up -d pool-mgt-ui
fi

echo ""
echo "Service started."
echo "  UI: http://localhost:$UI_PORT"
echo "  API: http://localhost:$PORT"
echo "  Docs: http://localhost:$PORT/docs"
echo ""
echo "API Key: $API_KEY"
echo ""
echo "Use './cicd/run.sh --logs' to view logs"
echo "Use './cicd/run.sh --stop' to stop"
