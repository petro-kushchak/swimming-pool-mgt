#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_DIR/VERSION"

usage() {
    echo "Usage: $0 [-v VERSION] [-t TAG] [--skip-tests] [--api-only] [--ui-only]"
    echo "  -v VERSION    Version to build (default: from VERSION file or required)"
    echo "  -t TAG        Additional tag to apply"
    echo "  --skip-tests  Skip running tests"
    echo "  --api-only    Build only API image"
    echo "  --ui-only     Build only UI image"
    exit 1
}

TAG=""
VERSION=""
SKIP_TESTS=false
BUILD_API=true
BUILD_UI=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests) SKIP_TESTS=true; shift ;;
        --api-only) BUILD_UI=false; shift ;;
        --ui-only) BUILD_API=false; shift ;;
        -v) VERSION="$2"; shift 2 ;;
        -t) TAG="$2"; shift 2 ;;
        -h) usage ;;
        *) echo "Unknown option: $1"; usage ;;
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

API_IMAGE_NAME="pool-mgt"
UI_IMAGE_NAME="pool-mgt-ui"
FULL_VERSION="${VERSION}"

if [ "$SKIP_TESTS" = false ] && [ "$BUILD_API" = true ]; then
    echo "Running tests..."
    docker build -f "$PROJECT_DIR/backend/Dockerfile.test" -t pool-mgt:test "$PROJECT_DIR" > /dev/null 2>&1
    
    if ! docker run --rm pool-mgt:test > /dev/null 2>&1; then
        echo "Tests failed!"
        docker rmi pool-mgt:test 2>/dev/null || true
        exit 1
    fi
    docker rmi pool-mgt:test 2>/dev/null || true
    echo "Tests passed."
    echo ""
fi

if [ "$BUILD_API" = true ]; then
    echo "Building ${API_IMAGE_NAME}:${FULL_VERSION}..."
    
    docker build -f "$PROJECT_DIR/docker/Dockerfile" \
        --build-arg BUILD_VERSION="${FULL_VERSION}" \
        -t "${API_IMAGE_NAME}:${FULL_VERSION}" "$PROJECT_DIR"
    
    if [ -n "$TAG" ]; then
        docker tag "${API_IMAGE_NAME}:${FULL_VERSION}" "${API_IMAGE_NAME}:${TAG}"
    fi
    
    echo "API build complete: ${API_IMAGE_NAME}:${FULL_VERSION}"
    echo ""
fi

if [ "$BUILD_UI" = true ]; then
    echo "Building ${UI_IMAGE_NAME}:${FULL_VERSION}..."
    
    docker build -f "$PROJECT_DIR/docker/Dockerfile.frontend" \
        --build-arg BUILD_VERSION="${FULL_VERSION}" \
        -t "${UI_IMAGE_NAME}:${FULL_VERSION}" "$PROJECT_DIR"
    
    if [ -n "$TAG" ]; then
        docker tag "${UI_IMAGE_NAME}:${FULL_VERSION}" "${UI_IMAGE_NAME}:${TAG}"
    fi
    
    echo "UI build complete: ${UI_IMAGE_NAME}:${FULL_VERSION}"
    echo ""
fi

echo "All builds complete!"
