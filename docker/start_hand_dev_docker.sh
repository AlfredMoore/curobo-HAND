#!/bin/bash
##
## Start the curobo-HAND dev container with local workspace mounted.
##
## This script mounts your local curobo-HAND repo into the container so you
## can edit code on the host and run it immediately inside the container.
##
## Usage:
##   bash docker/start_hand_dev_docker.sh [workspace_path] [image_tag]
##
## Arguments:
##   workspace_path  Absolute path to the curobo-HAND repo
##                   (default: directory two levels up from this script, i.e. the repo root)
##   image_tag       Docker image tag (default: latest)
##
## Examples:
##   bash docker/start_hand_dev_docker.sh
##   bash docker/start_hand_dev_docker.sh ~/robotics/curobo-HAND
##   bash docker/start_hand_dev_docker.sh ~/robotics/curobo-HAND 24.07-py3
##
## Inside the container:
##   The repo is available at /workspace/curobo-hand
##   To use your local curobo instead of the pre-installed upstream version:
##     cd /workspace/curobo-hand
##     pip install -e .[dev,usd] --no-build-isolation
##

set -e

# ── Resolve paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"   # curobo-HAND root

WORKSPACE="${1:-${REPO_ROOT}}"
IMAGE_TAG="${2:-latest}"
IMAGE_NAME="curobo_hand:${IMAGE_TAG}"

CONTAINER_WORKSPACE="/workspace/curobo-hand"

# ── Validate workspace ─────────────────────────────────────────────────────────
if [ ! -d "${WORKSPACE}" ]; then
    echo "[ERROR] Workspace not found: ${WORKSPACE}"
    echo "        Pass the correct path as the first argument."
    exit 1
fi

# ── X11 forwarding setup ───────────────────────────────────────────────────────
if [ -n "${DISPLAY}" ]; then
    xhost +local:docker 2>/dev/null || true
    X11_ARGS="-e DISPLAY=${DISPLAY} --volume /tmp/.X11-unix:/tmp/.X11-unix"
else
    X11_ARGS=""
fi

# ── Optional: additional mounts ────────────────────────────────────────────────
# Uncomment to mount your ~/data or model weights directory:
# DATA_MOUNT="--mount type=bind,src=${HOME}/data,target=/data"
DATA_MOUNT=""

echo "============================================="
echo " curobo-HAND dev container"
echo "  Image     : ${IMAGE_NAME}"
echo "  Workspace : ${WORKSPACE}"
echo "            → mounted at ${CONTAINER_WORKSPACE}"
echo "============================================="
echo ""
echo "TIP: To use your local curobo (instead of upstream):"
echo "  cd ${CONTAINER_WORKSPACE}"
echo "  pip install -e .[dev,usd] --no-build-isolation"
echo ""

docker run --rm -it \
    --privileged \
    --gpus all \
    --network host \
    --ipc host \
    -e NVIDIA_DISABLE_REQUIRE=1 \
    -e NVIDIA_DRIVER_CAPABILITIES=all \
    --device /dev/dri \
    ${X11_ARGS} \
    --volume /dev:/dev \
    --mount type=bind,src="${WORKSPACE}",target="${CONTAINER_WORKSPACE}" \
    ${DATA_MOUNT} \
    -w "${CONTAINER_WORKSPACE}" \
    "${IMAGE_NAME}" \
    bash --rcfile /etc/bash.bashrc
