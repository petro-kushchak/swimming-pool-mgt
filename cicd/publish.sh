#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_DIR/VERSION"
REGISTRY="${DOCKER_REGISTRY:-}"

usage() {
    echo "Usage: $0 -v VERSION [-r REGISTRY] [-t TAG] [-l]"
    echo "  -v VERSION   Version to publish (required)"
    echo "  -r REGISTRY  Docker registry (default: Docker Hub or DOCKER_REGISTRY env)"
    echo "  -t TAG       Additional tag to publish"
    echo "  -l           Also publish 'latest' tag"
    echo "  -d           Also publish 'dev' tag"
    exit 1
}

TAG=""
PUBLISH_LATEST=false
PUBLISH_DEV=false

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

IMAGE_NAME="swimming-pool-mgt"
TAGS=()

if [ -n "$REGISTRY" ]; then
    REGISTRY="${REGISTRY}/"
fi

FULL_IMAGE="${REGISTRY}${IMAGE_NAME}:${VERSION}"
TAGS+=("$FULL_IMAGE")

if [ "$PUBLISH_LATEST" = true ]; then
    TAGS+=("${REGISTRY}${IMAGE_NAME}:latest")
fi

if [ "$PUBLISH_DEV" = true ]; then
    TAGS+=("${REGISTRY}${IMAGE_NAME}:dev")
fi

if [ -n "$TAG" ]; then
    TAGS+=("${REGISTRY}${IMAGE_NAME}:${TAG}")
fi

echo "Publishing ${IMAGE_NAME}:${VERSION}..."
echo "Tags to publish:"
for t in "${TAGS[@]}"; do
    echo "  - $t"
done

for t in "${TAGS[@]}"; do
    echo "Pushing $t..."
    docker push "$t"
done

echo "Publish complete!"
