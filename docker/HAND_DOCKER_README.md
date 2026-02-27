# curobo-HAND Docker Guide

> A self-contained GPU environment for bimanual robot motion planning, computer vision, and ROS2.

> 一个集成双臂机器人运动规划、计算机视觉和ROS2的自包含GPU Docker环境。

---

## Table of Contents / 目录

1. [Overview / 概述](#1-overview--概述)
2. [Prerequisites / 前置条件](#2-prerequisites--前置条件)
3. [Image Architecture / 镜像层次结构](#3-image-architecture--镜像层次结构)
4. [Build / 构建镜像](#4-build--构建镜像)
5. [Run — Basic Mode / 启动（基础模式）](#5-run--basic-mode--启动基础模式)
6. [Run — Dev Mode / 启动（开发模式）](#6-run--dev-mode--启动开发模式)
7. [Installed Software / 已安装软件](#7-installed-software--已安装软件)
8. [TorchScript / JIT](#8-torchscript--jit)
9. [ROS2 Usage / ROS2使用](#9-ros2-usage--ros2使用)
10. [GPU Architecture / GPU架构参数](#10-gpu-architecture--gpu架构参数)
11. [Switching PyTorch Version / 切换PyTorch版本](#11-switching-pytorch-version--切换pytorch版本)
12. [Troubleshooting / 常见问题](#12-troubleshooting--常见问题)

---

## 1. Overview / 概述

This Docker setup provides a reproducible environment for the `curobo-HAND` project. It combines NVIDIA's optimized PyTorch NGC base image with CuRobo (GPU motion planning), ROS2 Humble (robot middleware), and popular CV libraries (YOLO, SAM2).

Two run modes are available:
- **Basic** — for running pre-installed scripts, no local files mounted.
- **Dev** — mounts your local repository so you can edit code on the host and run it immediately inside the container.

---

这套Docker配置为 `curobo-HAND` 项目提供可复现的运行环境，将NVIDIA优化的PyTorch NGC基础镜像与CuRobo（GPU运动规划）、ROS2 Humble（机器人中间件）和常用CV库（YOLO、SAM2）整合在一起。

提供两种启动模式：
- **基础模式** — 运行镜像内预装的脚本，不挂载本地文件。
- **开发模式** — 将本地仓库挂载进容器，在宿主机编辑代码，在容器内立即运行。

---

## 2. Prerequisites / 前置条件

| Requirement | Details |
|-------------|---------|
| NVIDIA GPU | Volta (V100) or newer recommended |
| NVIDIA Driver | ≥ 525 (for CUDA 12.x) |
| Docker Engine | ≥ 24 |
| NVIDIA Container Runtime | Required — see below |
| `xhost` (optional) | For GUI forwarding (rviz2, etc.) |

**Enable NVIDIA Container Runtime / 启用NVIDIA容器运行时**

Edit or create `/etc/docker/daemon.json`:

```json
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```

Then restart Docker:

```bash
sudo systemctl restart docker
```

---

| 前置条件 | 说明 |
|----------|------|
| NVIDIA GPU | 推荐Volta (V100)或更新架构 |
| NVIDIA驱动 | ≥ 525（CUDA 12.x需要） |
| Docker Engine | ≥ 24 |
| NVIDIA Container Runtime | 必须安装，见上方说明 |
| `xhost`（可选） | 用于转发GUI窗口（rviz2等） |

---

## 3. Image Architecture / 镜像层次结构

```
nvcr.io/nvidia/pytorch:24.07-py3
  │  Ubuntu 22.04 · PyTorch 2.4 · CUDA 12.5
  │
  └── hand.dockerfile
        ├── OpenGL / EGL          (visualization & headless rendering)
        ├── ROS2 Humble           (ros-base, vision_msgs, tf2, colcon)
        ├── CuRobo [dev, usd]     (GPU motion planning + USD export)
        └── CV stack
              ├── ultralytics     (YOLOv8 / v9 / v10 / v11)
              ├── SAM2 + SAM      (segment-anything-2)
              └── OpenCV, timm, einops, …
```

Final images produced / 构建后生成的镜像：

```
curobo_hand:24.07-py3   ← versioned tag / 带版本号标签
curobo_hand:latest      ← convenience alias / 便捷别名
```

---

## 4. Build / 构建镜像

Run from the **repository root** / 在**仓库根目录**下运行：

```bash
# Default: PyTorch 24.07-py3 (recommended)
# 默认：PyTorch 24.07-py3（推荐）
bash docker/build_hand_docker.sh

# Pin a specific PyTorch version / 指定PyTorch版本
bash docker/build_hand_docker.sh 24.01-py3
bash docker/build_hand_docker.sh 23.08-py3
```

> **Note / 注意**: Build time is roughly **20–40 minutes** depending on network speed and GPU count, as CuRobo requires CUDA compilation.
>
> 构建时间约 **20–40 分钟**，因为CuRobo需要CUDA编译，耗时取决于网络速度和GPU数量。

---

## 5. Run — Basic Mode / 启动（基础模式）

Use when you want to test pre-installed tools or run scripts already inside the image.

适用于测试预装工具，或运行已内置在镜像中的脚本。

```bash
bash docker/start_hand_docker.sh            # uses curobo_hand:latest
bash docker/start_hand_docker.sh 24.07-py3  # pin a specific version / 指定版本
```

Inside the container, a bash shell opens with ROS2 already sourced. Verify:

进入容器后，bash会自动source ROS2环境。验证：

```bash
# Check GPU / 检查GPU
python3 -c "import torch; print(torch.cuda.get_device_name(0))"

# Check CuRobo / 检查CuRobo
python3 -c "import curobo; print(curobo.__version__)"

# Check ROS2 / 检查ROS2
ros2 topic list
```

---

## 6. Run — Dev Mode / 启动（开发模式）

Mounts your local `curobo-HAND` repository into the container. Code edits on the host are immediately visible inside.

将本地 `curobo-HAND` 仓库挂载进容器。在宿主机修改代码，容器内立即可见。

```bash
# Auto-detect repo root (script is inside docker/, so goes two levels up)
# 自动推断仓库根目录（脚本位于docker/目录，自动向上两级）
bash docker/start_hand_dev_docker.sh

# Explicit path / 显式指定路径
bash docker/start_hand_dev_docker.sh ~/robotics/curobo-HAND

# Explicit path + specific image version / 指定路径和镜像版本
bash docker/start_hand_dev_docker.sh ~/robotics/curobo-HAND 24.07-py3
```

**Mount layout inside container / 容器内挂载结构：**

```
/workspace/curobo-hand/      ← your local repo / 你的本地仓库
    ├── docker/
    ├── examples/
    ├── robot_description/
    └── src/
```

**Use your local CuRobo instead of the pre-installed upstream version / 用本地CuRobo覆盖预装版本：**

```bash
# Inside the container / 在容器内执行
cd /workspace/curobo-hand
pip install -e .[dev,usd] --no-build-isolation
```

**Mount an extra data directory (e.g. model weights) / 挂载额外数据目录（如模型权重）：**

Uncomment the `DATA_MOUNT` line inside `start_hand_dev_docker.sh` and adjust the path:

取消注释 `start_hand_dev_docker.sh` 中的 `DATA_MOUNT` 行并修改路径：

```bash
DATA_MOUNT="--mount type=bind,src=${HOME}/data,target=/data"
```

---

## 7. Installed Software / 已安装软件

| Category / 类别 | Package / 包名 | Version / 版本 |
|-----------------|----------------|----------------|
| OS | Ubuntu | 22.04 (Jammy) |
| Deep Learning | PyTorch | 2.4 *(24.07-py3)* |
| GPU Compute | CUDA | 12.5 |
| Motion Planning | CuRobo | latest upstream |
| Robot Middleware | ROS2 Humble | ros-base + vision\_msgs + tf2 |
| Detection | Ultralytics YOLO | ≥ 8.2 |
| Segmentation | SAM2 (+ SAM1 fallback) | Meta Research |
| Vision | OpenCV (headless) | ≥ 4.9 |
| Vision | timm, einops, pillow | latest |
| Inference | TorchScript (torch.jit) | built-in |
| Rendering | OpenGL / EGL | system |

---

## 8. TorchScript / JIT

TorchScript works out of the box with the NGC image. No extra setup is needed.

NGC镜像已内置TorchScript，开箱即用，无需额外配置。

**Export YOLO to TorchScript / 将YOLO导出为TorchScript：**

```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
model.export(format="torchscript")   # produces yolov8n.torchscript
```

**Export / run a custom model / 导出或运行自定义模型：**

```python
import torch

# Trace a model (recommended for CV models with dynamic control flow)
# 跟踪模型（推荐用于含动态控制流的CV模型）
traced = torch.jit.trace(model, example_input)
torch.jit.save(traced, "model.pt")

# Script a model (for models with typed Python logic)
# 脚本化（适用于含类型化Python逻辑的模型）
scripted = torch.jit.script(model)
torch.jit.save(scripted, "model_scripted.pt")

# Load later / 后续加载
loaded = torch.jit.load("model.pt")
```

> **SAM2 note / SAM2注意**: The image encoder is traceable; the decoder uses dynamic shapes and is best run in eager mode or with `torch.compile`.
>
> SAM2的图像编码器可以trace，解码器使用动态shape，建议以eager模式运行或使用 `torch.compile`。

---

## 9. ROS2 Usage / ROS2使用

ROS2 Humble is automatically sourced for every new bash session via `/etc/bash.bashrc`.

ROS2 Humble通过 `/etc/bash.bashrc` 在每次新的bash会话中自动source。

```bash
# Verify ROS2 / 验证ROS2
ros2 topic list
ros2 doctor

# Build a colcon workspace / 构建colcon工作空间
mkdir -p ~/ros_ws/src && cd ~/ros_ws
colcon build --symlink-install
source install/setup.bash

# If a new shell doesn't have ROS2 / 若新shell中没有ROS2
source /opt/ros/humble/setup.bash
```

**Key packages pre-installed / 已预装的关键包：**

| Package | Use case / 用途 |
|---------|-----------------|
| `ros-humble-ros-base` | Core ROS2 / ROS2核心 |
| `ros-humble-vision-msgs` | Standard CV message types / 标准CV消息类型 |
| `ros-humble-tf2-ros` | Transform tree / 坐标变换树 |
| `ros-humble-sensor-msgs` | Image, PointCloud2, etc. / 图像、点云等 |
| `ros-humble-geometry-msgs` | Pose, Twist, etc. / 位姿、速度等 |

---

## 10. GPU Architecture / GPU架构参数

The dockerfile sets:

```dockerfile
ENV TORCH_CUDA_ARCH_LIST="7.0+PTX"
```

This compiles CuRobo's CUDA extensions for **Volta (V100) and newer** (via PTX JIT for Ampere, Hopper, etc.).

这会将CuRobo的CUDA扩展编译为支持 **Volta (V100) 及更新架构**（通过PTX JIT支持Ampere、Hopper等）。

**To optimize build time for a specific GPU / 针对特定GPU优化构建时间：**

Edit `hand.dockerfile` before building: 构建前编辑 `hand.dockerfile`：

```dockerfile
# RTX 3090 / A5000 / A6000 (Ampere)
ENV TORCH_CUDA_ARCH_LIST="8.6"

# RTX 4090 / A100 (Ampere 80 / Ada)
ENV TORCH_CUDA_ARCH_LIST="8.0;8.9"

# Keep broad compatibility (default)
ENV TORCH_CUDA_ARCH_LIST="7.0+PTX"
```

---

## 11. Switching PyTorch Version / 切换PyTorch版本

Pass the NGC tag as the first argument to `build_hand_docker.sh`:

将NGC标签作为第一个参数传给 `build_hand_docker.sh`：

```bash
bash docker/build_hand_docker.sh 24.07-py3   # PyTorch 2.4, CUDA 12.5
bash docker/build_hand_docker.sh 24.01-py3   # PyTorch 2.2, CUDA 12.3
bash docker/build_hand_docker.sh 23.08-py3   # PyTorch 2.0, CUDA 12.1
```

| NGC Tag | PyTorch | CUDA | Ubuntu | Notes / 说明 |
|---------|---------|------|--------|--------------|
| `24.07-py3` | 2.4 | 12.5 | 22.04 | **Recommended / 推荐** · SAM2 ✓ |
| `24.01-py3` | 2.2 | 12.3 | 22.04 | Balanced / 均衡选择 · SAM2 ✓ |
| `23.08-py3` | 2.0 | 12.1 | 22.04 | CuRobo official test version / CuRobo官方测试版本 · SAM2 ✗ |

> All three tags use **Ubuntu 22.04**, so ROS2 Humble is compatible with all of them.
>
> 三个标签都基于 **Ubuntu 22.04**，因此ROS2 Humble与所有版本兼容。

> **SAM2 requires PyTorch ≥ 2.3.1.** With `23.08-py3` (PyTorch 2.0), the dockerfile falls back to SAM1 automatically.
>
> **SAM2需要PyTorch ≥ 2.3.1。** 使用 `23.08-py3`（PyTorch 2.0）时，dockerfile会自动回退到SAM1。

---

## 12. Troubleshooting / 常见问题

| Problem / 问题 | Solution / 解决方案 |
|----------------|---------------------|
| `nvidia-container-runtime` not found during build | Enable in `/etc/docker/daemon.json` (see §2), restart Docker |
| NVIDIA运行时未找到 | 在 `/etc/docker/daemon.json` 中启用（见第2节），重启Docker |
| `CUDA not available` at runtime | Make sure you used `bash start_hand_docker.sh` (which passes `--gpus all`) — not plain `docker run` |
| 运行时CUDA不可用 | 确保使用 `bash start_hand_docker.sh`（包含 `--gpus all`），不要直接用 `docker run` |
| `ros2: command not found` | Run: `source /opt/ros/humble/setup.bash` |
| ROS2命令找不到 | 执行：`source /opt/ros/humble/setup.bash` |
| GUI window not appearing | On host, run `xhost +local:docker` before starting the container |
| GUI窗口不显示 | 在宿主机上先运行 `xhost +local:docker`，再启动容器 |
| `empy` version conflict during ROS2 build | Already fixed in the dockerfile (`empy==3.3.4`). If it reappears: `pip install empy==3.3.4` |
| ROS2构建时empy版本冲突 | dockerfile已修复（`empy==3.3.4`）。若复现：`pip install empy==3.3.4` |
| `SAM2` install fails | dockerfile falls back to SAM1 automatically; check Python / PyTorch version |
| SAM2安装失败 | dockerfile自动回退到SAM1；检查Python和PyTorch版本 |
| Workspace not found (dev mode) | Pass the absolute path explicitly: `bash start_hand_dev_docker.sh /absolute/path/to/curobo-HAND` |
| 开发模式找不到工作区 | 显式传入绝对路径：`bash start_hand_dev_docker.sh /absolute/path/to/curobo-HAND` |

---

## File Reference / 文件说明

```
docker/
├── hand.dockerfile              # Image definition / 镜像定义
├── build_hand_docker.sh         # Build script / 构建脚本
├── start_hand_docker.sh         # Basic runner / 基础启动
├── start_hand_dev_docker.sh     # Dev runner (with workspace mount) / 开发启动（挂载工作区）
└── HAND_DOCKER_README.md        # This document / 本文档
```
