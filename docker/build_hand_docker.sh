#!/bin/bash
##
## Build the curobo-HAND docker image.
##
## Usage:
##   bash docker/build_hand_docker.sh [pytorch_tag]
##
## Arguments:
##   pytorch_tag  NGC PyTorch image tag (default: 24.07-py3)
##                Other options: 23.08-py3, 24.01-py3, 24.04-py3
##
## Examples:
##   bash docker/build_hand_docker.sh               # uses 24.07-py3
##   bash docker/build_hand_docker.sh 24.01-py3     # pin an older version
##

set -e

PYTORCH_TAG="${1:-24.07-py3}"
IMAGE_NAME="curobo_hand"
IMAGE_TAG="${PYTORCH_TAG}"
FULL_TAG="${IMAGE_NAME}:${IMAGE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================="
echo " Building curobo-HAND docker image"
echo "  PyTorch tag : ${PYTORCH_TAG}"
echo "  Image       : ${FULL_TAG}"
echo "============================================="

# Verify NVIDIA runtime is available
if ! docker info 2>/dev/null | grep -q "nvidia"; then
    echo ""
    echo "[WARN] NVIDIA runtime not detected in docker info."
    echo "       If build fails on CUDA steps, enable it in /etc/docker/daemon.json:"
    echo '       { "default-runtime": "nvidia", "runtimes": { "nvidia": { "path": "/usr/bin/nvidia-container-runtime", "runtimeArgs": [] } } }'
    echo ""
fi

docker build \
    --build-arg PYTORCH_IMAGE_TAG="${PYTORCH_TAG}" \
    --build-arg CACHE_DATE="$(date +%Y-%m-%d)" \
    -t "${FULL_TAG}" \
    -t "${IMAGE_NAME}:latest" \
    -f "${SCRIPT_DIR}/hand.dockerfile" \
    "${SCRIPT_DIR}"

echo ""
echo "============================================="
echo " Build complete: ${FULL_TAG}"
echo " Also tagged as: ${IMAGE_NAME}:latest"
echo "============================================="
echo ""
echo "Next steps:"
echo "  Start basic container    : bash docker/start_hand_docker.sh"
echo "  Start dev container      : bash docker/start_hand_dev_docker.sh"
