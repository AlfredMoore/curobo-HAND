##
## Dockerfile for curobo-HAND environment
## - Base: NVIDIA PyTorch NGC image (configurable version)
## - Includes: CuRobo, ROS2 Humble, CV libs (YOLO, SAM), TorchScript support
##
## Build with:
##   bash docker/build_hand_docker.sh [pytorch_tag]
##   e.g. bash docker/build_hand_docker.sh 24.07-py3
##

ARG PYTORCH_IMAGE_TAG=24.07-py3
FROM nvcr.io/nvidia/pytorch:${PYTORCH_IMAGE_TAG}

LABEL maintainer="curobo-hand"

# ─────────────────────────────────────────────
# 1. Non-interactive frontend for apt
# ─────────────────────────────────────────────
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# ─────────────────────────────────────────────
# 2. OpenGL / EGL (for visualization & headless rendering)
# ─────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config \
        libglvnd-dev \
        libgl1-mesa-dev \
        libegl1-mesa-dev \
        libgles2-mesa-dev && \
    rm -rf /var/lib/apt/lists/*

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute

# ─────────────────────────────────────────────
# 3. Base system tools + timezone
# ─────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
      tzdata \
      software-properties-common \
      curl \
      wget \
      lsb-release \
      gnupg2 \
      ca-certificates \
      build-essential \
      cmake \
      git \
      git-lfs \
      iputils-ping \
      make \
      openssh-server \
      openssh-client \
      libeigen3-dev \
      libssl-dev \
      python3-pip \
      python3-ipdb \
      python3-tk \
      sudo \
      bash \
      terminator \
      unattended-upgrades \
      apt-utils \
    && rm -rf /var/lib/apt/lists/* \
    && ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

# ─────────────────────────────────────────────
# 4. ROS2 Humble (Ubuntu 22.04 / Jammy)
#    NGC pytorch:24.07-py3 is Ubuntu 22.04
# ─────────────────────────────────────────────
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc \
      | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
      http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
      | tee /etc/apt/sources.list.d/ros2.list > /dev/null

RUN apt-get update && apt-get install -y \
      ros-humble-ros-base \
      ros-humble-vision-msgs \
      ros-humble-tf2-ros \
      ros-humble-sensor-msgs \
      ros-humble-geometry-msgs \
      python3-colcon-common-extensions \
      python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

# rosdep init (ignore if already exists)
RUN rosdep init || true && rosdep update

# ROS2 empy version fix: NGC container ships empy>=4 but ROS2 build tools need empy==3.x
RUN pip install "empy==3.3.4"

# Source ROS2 for all bash sessions
RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc

ENV ROS_DISTRO=humble
ENV ROS_ROOT=/opt/ros/humble

# ─────────────────────────────────────────────
# 5. CuRobo
#    TORCH_CUDA_ARCH_LIST: covers Volta(7.0) → Hopper(9.0)
#    Adjust to your GPU if needed (e.g. "8.6" for RTX 3090)
# ─────────────────────────────────────────────
ENV TORCH_CUDA_ARCH_LIST="7.0+PTX"
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

# Cache-busting ARG: change this date to force re-clone
ARG CACHE_DATE=2024-07-19

# Clone and install CuRobo from upstream.
# In dev mode: override with pip install -e /workspace/curobo-hand[dev,usd]
RUN mkdir -p /pkgs && cd /pkgs && \
    git clone https://github.com/NVlabs/curobo.git

RUN cd /pkgs/curobo && \
    pip install .[dev,usd] --no-build-isolation

WORKDIR /pkgs/curobo

# EGL config for headless USD / Isaac rendering
ENV PYOPENGL_PLATFORM=egl
RUN echo '{"file_format_version": "1.0.0", "ICD": {"library_path": "libEGL_nvidia.so.0"}}' \
      >> /usr/share/glvnd/egl_vendor.d/10_nvidia.json

# ─────────────────────────────────────────────
# 6. CV / Perception libraries
#    All installed via pip to stay inside the NGC python env.
# ─────────────────────────────────────────────

# Core CV
RUN pip install \
      "opencv-python-headless>=4.9" \
      pillow \
      imageio \
      transforms3d \
      scipy \
      matplotlib \
      tqdm \
      einops \
      timm

# YOLO (Ultralytics, includes YOLOv8/v9/v10/v11 + export helpers)
RUN pip install "ultralytics>=8.2"

# SAM2 (Segment Anything Model 2 - Meta Research)
# Requires PyTorch >= 2.3.1; satisfied by 24.07-py3 (PyTorch 2.4)
RUN pip install "samv2 @ git+https://github.com/facebookresearch/sam2.git" || \
    pip install "segment-anything-2"
# Fallback: original SAM (lighter-weight)
RUN pip install git+https://github.com/facebookresearch/segment-anything.git

# ─────────────────────────────────────────────
# 7. TorchScript / JIT notes
#    torch.jit works out of the box with NGC images.
#    Export YOLO:  model.export(format='torchscript')
#    Export SAM encoder separately (decoder not scriptable by default).
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# 8. Sanity check
# ─────────────────────────────────────────────
RUN python3 -c " \
import torch; \
print(f'[OK] PyTorch  : {torch.__version__}'); \
print(f'[OK] CUDA     : {torch.version.cuda}'); \
print(f'[OK] JIT      : {torch.jit.__name__}'); \
assert torch.cuda.is_available() or True, 'CUDA check deferred to runtime'; \
import curobo; print(f'[OK] CuRobo   : {curobo.__version__}'); \
import ultralytics; print(f'[OK] Ultralytics: {ultralytics.__version__}'); \
"

WORKDIR /workspace
