#!/bin/bash
##
## Start the curobo-HAND docker container (no code mount).
## Useful for quick tests or running pre-baked scripts inside the image.
##
## Usage:
##   bash docker/start_hand_docker.sh [image_tag]
##
## Arguments:
##   image_tag  Docker image tag (default: latest)
##
## Examples:
##   bash docker/start_hand_docker.sh
##   bash docker/start_hand_docker.sh 24.07-py3
##

set -e

IMAGE_TAG="${1:-latest}"
IMAGE_NAME="curobo_hand:${IMAGE_TAG}"

# ── X11 forwarding setup (for GUI tools like rviz2, usdview) ──────────────────
if [ -n "${DISPLAY}" ]; then
    xhost +local:docker 2>/dev/null || true
    X11_ARGS="-e DISPLAY=${DISPLAY} --volume /tmp/.X11-unix:/tmp/.X11-unix"
else
    X11_ARGS=""
fi

echo "Starting: ${IMAGE_NAME}"

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
    "${IMAGE_NAME}" \
    bash --rcfile /etc/bash.bashrc
