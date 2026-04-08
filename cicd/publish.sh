#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_DIR/VERSION"
REGISTRY="${DOCKER_REGISTRY:-}"

usage() {
    echo "Usage: $0 -v VERSION [-r REGISTRY] [-t TAG] [-l] [-d] [--api-only] [--ui-only]"
    echo "  -v VERSION   Version to publish (required)"
    echo "  -r REGISTRY  Docker registry (default: Docker Hub or DOCKER_REGISTRY env)"
    echo "  -t TAG       Additional tag to publish"
    echo "  -l           Also publish 'latest' tag"
    echo "  -d           Also publish 'dev' tag"
    echo "  --api-only   Publish only API image"
    echo "  --ui-only    Publish only UI image"
    exit 1
}

TAG=""
PUBLISH_LATEST=false
PUBLISH_DEV=false
PUBLISH_API=true
PUBLISH_UI=true

for arg in "$@"; do
    case "$arg" in
        --api-only) PUBLISH_UI=false ;;
        --ui-only) PUBLISH_API=false ;;
    esac
done

while getopts "v:r:t:ldh" opt; do
    case $opt in
        v) VERSION="$OPTARG" ;;
        r) REGISTRY="$OPTARG" ;;
        t) TAG="$OPTARG" ;;
        l) PUBLISH_LATEST=true ;;
        d) PUBLISH_DEV=true ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "Error: Version is required (-v)"
    exit 1
fi

if [ -z "$REGISTRY" ]; then
    REGISTRY=""
else
    REGISTRY="${REGISTRY}/"
fi

publish_image() {
    local image_name=$1
    local tags=("${@:2}")
    
    for t in "${tags[@]}"; do
        echo "Pushing ${t}..."
        docker push "$t"
    done
}

if [ "$PUBLISH_API" = true ]; then
    API_IMAGE_NAME="pool-mgt"
    
    API_TAGS=()
    FULL_API_IMAGE="${REGISTRY}${API_IMAGE_NAME}:${VERSION}"
    API_TAGS+=("$FULL_API_IMAGE")
    
    if [ "$PUBLISH_LATEST" = true ]; then
        API_TAGS+=("${REGISTRY}${API_IMAGE_NAME}:latest")
    fi
    
    if [ "$PUBLISH_DEV" = true ]; then
        API_TAGS+=("${REGISTRY}${API_IMAGE_NAME}:dev")
    fi
    
    if [ -n "$TAG" ]; then
        API_TAGS+=("${REGISTRY}${API_IMAGE_NAME}:${TAG}")
    fi
    
    echo "Publishing ${API_IMAGE_NAME}:${VERSION}..."
    echo "Tags:"
    for t in "${API_TAGS[@]}"; do
        echo "  - $t"
    done
    
    publish_image "${API_IMAGE_NAME}" "${API_TAGS[@]}"
    echo ""
fi

if [ "$PUBLISH_UI" = true ]; then
    UI_IMAGE_NAME="pool-mgt-ui"
    
    UI_TAGS=()
    FULL_UI_IMAGE="${REGISTRY}${UI_IMAGE_NAME}:${VERSION}"
    UI_TAGS+=("$FULL_UI_IMAGE")
    
    if [ "$PUBLISH_LATEST" = true ]; then
        UI_TAGS+=("${REGISTRY}${UI_IMAGE_NAME}:latest")
    fi
    
    if [ "$PUBLISH_DEV" = true ]; then
        UI_TAGS+=("${REGISTRY}${UI_IMAGE_NAME}:dev")
    fi
    
    if [ -n "$TAG" ]; then
        UI_TAGS+=("${REGISTRY}${UI_IMAGE_NAME}:${TAG}")
    fi
    
    echo "Publishing ${UI_IMAGE_NAME}:${VERSION}..."
    echo "Tags:"
    for t in "${UI_TAGS[@]}"; do
        echo "  - $t"
    done
    
    publish_image "${UI_IMAGE_NAME}" "${UI_TAGS[@]}"
    echo ""
fi

echo "Publish complete!"
