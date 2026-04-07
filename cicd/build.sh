#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_DIR/VERSION"
DOCKERFILE="$PROJECT_DIR/docker/Dockerfile"

usage() {
    echo "Usage: $0 [-v VERSION] [-t TAG] [--skip-tests]"
    echo "  -v VERSION    Version to build (default: from VERSION file or required)"
    echo "  -t TAG       Additional tag to apply"
    echo "  --skip-tests Skip running tests"
    exit 1
}

TAG=""
VERSION=""
SKIP_TESTS=false

for arg in "$@"; do
    case "$arg" in
        --skip-tests) SKIP_TESTS=true ;;
    esac
done

while getopts "v:t:h" opt; do
    case $opt in
        v) VERSION="$OPTARG" ;;
        t) TAG="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [ -z "$VERSION" ]; then
    if [ -f "$VERSION_FILE" ]; then
        VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
    else
        echo "Error: Version not specified and VERSION file not found"
        exit 1
    fi
fi

IMAGE_NAME="swimming-pool-mgt"
FULL_VERSION="${VERSION}"
TAG_ARG="${IMAGE_NAME}:${FULL_VERSION}"

if [ -n "$TAG" ]; then
    TAG_ARG="${TAG_ARG} ${IMAGE_NAME}:${TAG}"
fi

if [ "$SKIP_TESTS" = false ]; then
    echo "Running tests..."
    docker build -f "$PROJECT_DIR/backend/Dockerfile.test" -t pool-mgt:test "$PROJECT_DIR" > /dev/null 2>&1
    
    if ! docker run --rm pool-mgt:test; then
        echo "Tests failed!"
        docker rmi pool-mgt:test 2>/dev/null || true
        exit 1
    fi
    docker rmi pool-mgt:test 2>/dev/null || true
    echo "Tests passed."
    echo ""
fi

echo "Building ${IMAGE_NAME}:${FULL_VERSION}..."

docker build -f "$DOCKERFILE" \
    --build-arg BUILD_VERSION="${FULL_VERSION}" \
    -t "${IMAGE_NAME}:${FULL_VERSION}" "$PROJECT_DIR"

if [ -n "$TAG" ]; then
    docker tag "${IMAGE_NAME}:${FULL_VERSION}" "${IMAGE_NAME}:${TAG}"
fi

echo "Build complete: ${IMAGE_NAME}:${FULL_VERSION}"
