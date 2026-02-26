<!--
Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
property and proprietary rights in and to this material, related
documentation and any modifications thereto. Any use, reproduction,
disclosure or distribution of this material and related documentation
without an express license agreement from NVIDIA CORPORATION or
its affiliates is strictly prohibited.
-->
# Installation Tips (Zh中文)

本指南主要解决在独立 Conda 虚拟环境（如 `env_isaaclab`）中安装 cuRobo 时常见的 **CUDA 编译器路径缺失**、**头文件找不到 (cuda_runtime.h)** 以及 **C++ 标准库版本冲突** 等问题。

---

## 📋 核心问题复盘

在 Isaac Lab 或类似的 Conda 环境中，直接运行 `pip install -e .` 通常会失败，主要原因如下：

1.  **编译器缺失**：PyTorch 分发的 CUDA 仅包含 Runtime 库，不包含编译自定义 C++/CUDA 算子所需的 `nvcc`。
2.  **路径深埋**：Conda 安装的 `cuda-toolkit` 并没有将头文件放在标准路径，而是存放在：`$CONDA_PREFIX/targets/x86_64-linux/include`。
3.  **环境冲突**：Conda 环境内的 `libstdc++.so.6` 版本可能低于编译工具（如 `ninja`）的需求。



---

## 🛠️ 1. 环境准备 (环境内补全)

首先需要在激活的 Conda 环境中，安装完整的开发工具链。建议版本与你的显卡驱动及 PyTorch 支持版本匹配（示例为 CUDA 12.4）。

```bash
# 安装编译器、开发头文件及构建工具
conda install -c nvidia cuda-nvcc=12.4 cuda-toolkit=12.4

# 修复 GLIBCXX 版本冲突 (解决 ninja 无法运行的问题)
conda install -c conda-forge libstdcxx-ng
```

---

### 第三部分：安装命令（最核心部分）
```markdown
## 🚀 2. 编译与安装步骤

为了让编译器能够“看见”深埋在 Conda 目录中的头文件，必须在编译前手动注入环境变量。
应该不需要那么多环境变量，本模块暂时未经测试。
```bash
# 1. 进入项目根目录
cd /path/to/curobo-HAND

# 2. 设置 CUDA 根目录变量
export CUDA_HOME=$CONDA_PREFIX
export PATH=$CONDA_PREFIX/bin:$PATH

# 3. 显式注入深层头文件路径 (解决 fatal error: cuda_runtime_api.h 找不到的问题)
export CPATH=$CONDA_PREFIX/targets/x86_64-linux/include:$CPATH
export C_INCLUDE_PATH=$CONDA_PREFIX/targets/x86_64-linux/include:$C_INCLUDE_PATH
export CPLUS_INCLUDE_PATH=$CONDA_PREFIX/targets/x86_64-linux/include:$CPLUS_INCLUDE_PATH

# 4. 注入动态库搜索路径 (运行时必须)
export LD_LIBRARY_PATH=$CONDA_PREFIX/targets/x86_64-linux/lib:$CONDA_PREFIX/lib:$LD_LIBRARY_PATH

# 5. 清理旧的编译残余 (如果存在该文件夹的话，非常重要)
rm -rf build/ src/*.egg-info/

# 6. 执行带路径参数的安装
CFLAGS="-I$CONDA_PREFIX/targets/x86_64-linux/include" \
LDFLAGS="-L$CONDA_PREFIX/targets/x86_64-linux/lib" \
pip install -e . --no-build-isolation
```

---

### 第四部分：报错排查表格
## 🔍 3. 常见报错排查 (Troubleshooting)

| 报错信息 | 可能原因 | 解决方法 |
| :--- | :--- | :--- |
| `cuda_runtime.h: No such file` | 编译器默认搜索路径不包含 `targets` 目录 | 确保已执行上述 `export CPATH` 步骤或在 `pip` 时传入 `CFLAGS`。 |
| `GLIBCXX_3.4.32 not found` | 编译工具链与环境内 C++ 标准库版本不匹配 | 运行 `conda install libstdcxx-ng`。 |
| `CUDA_HOME not set` | 编译脚本找不到 CUDA 安装根目录 | 执行 `export CUDA_HOME=$CONDA_PREFIX`。 |
| `ninja: build stopped` | 可能是内存不足或并行冲突 | 尝试在命令前加 `MAX_JOBS=4` 限制并行编译数。 |

<!-- ## 🔄 4. 持久化配置 (推荐)

为避免每次打开新终端都要重复设置，建议将动态库路径持久化到 Conda 环境配置中：

```bash
# 这样每次 conda activate 该环境时，库路径会自动补全
conda env config vars set LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$CONDA_PREFIX/targets/x86_64-linux/lib -->

# cuRobo

*CUDA Accelerated Robot Library*

**Check [curobo.org](https://curobo.org) for installing and getting started with examples!**

Use [Discussions](https://github.com/NVlabs/curobo/discussions) for questions on using this package.

Use [Issues](https://github.com/NVlabs/curobo/issues) if you find a bug.


cuRobo's collision-free motion planner is available for commercial applications as a
MoveIt plugin: [Isaac ROS cuMotion](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_cumotion)

For business inquiries of this python library, please visit our website and submit the form: [NVIDIA Research Licensing](https://www.nvidia.com/en-us/research/inquiries/)


## Overview

cuRobo is a CUDA accelerated library containing a suite of robotics algorithms that run significantly faster than existing implementations leveraging parallel compute. cuRobo currently provides the following algorithms: (1) forward and inverse kinematics,
(2) collision checking between robot and world, with the world represented as Cuboids, Meshes, and Depth images, (3) numerical optimization with gradient descent, L-BFGS, and MPPI, (4) geometric planning, (5) trajectory optimization, (6) motion generation that combines inverse kinematics, geometric planning, and trajectory optimization to generate global motions within 30ms.

<p align="center">
<img width="500" src="images/robot_demo.gif">
</p>


cuRobo performs trajectory optimization across many seeds in parallel to find a solution. cuRobo's trajectory optimization penalizes jerk and accelerations, encouraging smoother and shorter trajectories. Below we compare cuRobo's motion generation on the left to a BiRRT planner for the motion planning phases in a pick and place task.

<p align="center">
<img width="500" src="images/rrt_compare.gif">
</p>


## Citation

If you found this work useful, please cite the below report,

```
@misc{curobo_report23,
      title={cuRobo: Parallelized Collision-Free Minimum-Jerk Robot Motion Generation},
      author={Balakumar Sundaralingam and Siva Kumar Sastry Hari and Adam Fishman and Caelan Garrett
              and Karl Van Wyk and Valts Blukis and Alexander Millane and Helen Oleynikova and Ankur Handa
              and Fabio Ramos and Nathan Ratliff and Dieter Fox},
      year={2023},
      eprint={2310.17274},
      archivePrefix={arXiv},
      primaryClass={cs.RO}
}
```