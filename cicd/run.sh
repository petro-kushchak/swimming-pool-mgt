#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_DIR/VERSION"
IMAGE_NAME="swimming-pool-mgt"

usage() {
    echo "Usage: $0 [-v VERSION] [-d POOLS_CONFIG] [-i INTERVAL] [-p PORT] [-b] [-r] [--stop] [--logs]"
    echo ""
    echo "Options:"
    echo "  -v VERSION       Version to build/run (default: from VERSION file)"
    echo "  -d POOLS_CONFIG Path to pools.json (default: ./pools.json)"
    echo "  -i INTERVAL     Scheduler interval in seconds (default: 60)"
    echo "  -p PORT         API port to expose (default: 8000)"
    echo "  -b              Build image before running"
    echo "  -r              Remove existing container before running"
    echo "  --stop          Stop and remove running container"
    echo "  --logs          Show container logs"
    exit 1
}

VERSION=""
STOP=false
BUILD=false
REMOVE=false
SHOW_LOGS=false
PORT=8000
POOLS_CONFIG="./pools.json"
INTERVAL=60

for arg in "$@"; do
    case "$arg" in
        --stop) STOP=true ;;
        --logs) SHOW_LOGS=true ;;
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

while getopts "v:d:i:p:brh" opt; do
    case $opt in
        v) VERSION="$OPTARG" ;;
        d) POOLS_CONFIG="$OPTARG" ;;
        i) INTERVAL="$OPTARG" ;;
        p) PORT="$OPTARG" ;;
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

if [ "$BUILD" = true ]; then
    if [ -z "$VERSION" ]; then
        echo "Error: Version required for build"
        exit 1
    fi
    echo "Building image ${IMAGE_NAME}:${VERSION}..."
    cd "$PROJECT_DIR" && ./cicd/build.sh -v "$VERSION"
fi

cd "$PROJECT_DIR"

POOLS_CONFIG_ABS=$(realpath "$POOLS_CONFIG" 2>/dev/null || echo "$POOLS_CONFIG")

echo "Starting Swimming Pool Management Service..."
echo "  Version: ${VERSION:-latest}"
echo "  API Port: $PORT"
echo "  Pools config: $POOLS_CONFIG_ABS"
echo "  Scheduler interval: ${INTERVAL}s"
echo ""

export BUILD_VERSION="${VERSION:-unknown}"
export API_PORT="$PORT"
export POOLS_CONFIG="$POOLS_CONFIG_ABS"
export SCHEDULER_INTERVAL="$INTERVAL"
export COMPOSE_PROJECT_NAME="pool-mgt"

docker compose up -d

echo ""
echo "Service started."
echo "  API: http://localhost:$PORT"
echo "  Docs: http://localhost:$PORT/docs"
echo ""
echo "Use './cicd/run.sh --logs' to view logs"
echo "Use './cicd/run.sh --stop' to stop"
