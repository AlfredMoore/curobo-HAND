# 双臂Panda+Tesollo系统快速开始指南

## 📦 已创建的文件

### 1. URDF生成工具
```bash
robot_description/composites/generate_bimanual_panda_tesollo.py
```
- 从单臂URDF生成双臂URDF的Python脚本
- 可复用，参数可调

### 2. 双臂URDF
```bash
robot_description/rl/bimanual_panda_tesollo.urdf
```
- 不包含桌子（桌子在world config中）
- 38自由度：2 × (7臂关节 + 12手爪关节)
- 左右臂位置参考了 `bimanual_arms.urdf`

### 3. CuRobo配置文件
```bash
# Robot配置
robot_description/configs/robot/bimanual_panda_tesollo.yml

# 碰撞球配置
robot_description/configs/robot/spheres/bimanual_panda_tesollo.yml

# World配置（含桌子）
robot_description/configs/world/bimanual_table.yml
```

### 4. 示例代码
```bash
examples/bimanual_motion_gen_example.py          # 双臂运动规划示例
examples/visualize_spheres_official.py           # 碰撞球可视化（官方方法）
examples/visualize_collision_spheres.py          # 碰撞球静态可视化
```

### 5. 工具脚本
```bash
tools/generate_hand_spheres.py                   # 基于URDF生成手部sphere配置
```

### 6. 文档
```bash
examples/BIMANUAL_README.md                      # 详细英文文档
examples/VISUALIZATION_GUIDE.md                  # 可视化完整指南
robot_description/configs/README.md              # 配置文件说明
BIMANUAL_QUICK_START.md                          # 本文件（中文快速指南）
```

---

## 🚀 快速使用

### 1. 运行双臂运动规划示例
```bash
python examples/bimanual_motion_gen_example.py
```

**输出：**
- 控制台显示规划结果
- `bimanual_trajectory.usd` - 包含轨迹和碰撞球的可视化文件

### 2. 可视化碰撞球（Collision Spheres）
```bash
# 静态可视化（官方方法）
python examples/visualize_spheres_official.py

# 带动画的可视化
python examples/visualize_spheres_official.py motion

# 查看sphere配置统计
python examples/visualize_spheres_official.py stats
```

**输出：**
- `bimanual_spheres.usd` - USD文件，可在Isaac Sim或在线viewer中查看

### 3. 基本代码示例

```python
import torch
from curobo.types.base import TensorDeviceType
from curobo.types.math import Pose
from curobo.types.robot import JointState
from curobo.wrap.reacher.motion_gen import MotionGen, MotionGenConfig

# 初始化
tensor_args = TensorDeviceType(device=torch.device("cuda:0"))

# 加载配置
motion_gen_cfg = MotionGenConfig.load_from_robot_config(
    robot_cfg="robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
    world_cfg="robot/robot_description/configs/world/bimanual_table.yml",
    tensor_args=tensor_args,
)

motion_gen = MotionGen(motion_gen_cfg)
motion_gen.warmup()

# 设置起始配置（38个关节）
q_start = motion_gen.get_retract_config()

# 设置目标位姿
# 左臂目标（主要EE）
left_goal = Pose(
    position=tensor_args.to_device([[0.5, 0.3, 1.0]]),
    quaternion=tensor_args.to_device([[1, 0, 0, 0]]),
)

# 右臂目标（使用link_poses）
link_poses = {
    "right_delto_base_link": Pose(
        position=tensor_args.to_device([[0.5, -0.3, 1.0]]),
        quaternion=tensor_args.to_device([[1, 0, 0, 0]]),
    )
}

# 规划轨迹
result = motion_gen.plan_single(
    q_start,
    left_goal,
    link_poses=link_poses  # 指定右臂目标
)

if result.success.item():
    trajectory = result.get_interpolated_plan()
    print(f"成功！轨迹有 {len(trajectory.position)} 步")
```

---

## 🔧 关键概念

### 1. 双臂坐标系
- **Base link**: `world`
- **左臂EE**: `left_delto_base_link`（主EE，手掌base）
- **右臂EE**: `right_delto_base_link`
- **可用EE列表**: `link_names: ["left_delto_base_link", "right_delto_base_link"]`

**注意**：使用 `delto_base_link` 而非 `F1_TIP_TOP`（指尖），这与franka.yml中使用 `panda_hand` 的模式一致。

### 2. 关节配置（38 DoF）

```python
joint_order = [
    # 左臂 (7)
    'left_panda_joint1', ..., 'left_panda_joint7',

    # 左手爪 (12 = 3手指 × 4关节)
    'left_F1M1', 'left_F1M2', 'left_F1M3', 'left_F1M4',  # 手指1
    'left_F2M1', 'left_F2M2', 'left_F2M3', 'left_F2M4',  # 手指2
    'left_F3M1', 'left_F3M2', 'left_F3M3', 'left_F3M4',  # 手指3

    # 右臂 (7)
    'right_panda_joint1', ..., 'right_panda_joint7',

    # 右手爪 (12)
    'right_F1M1', ..., 'right_F3M4',
]
```

### 3. 桌子在World Config中
✓ **正确做法**：桌子在 `robot_description/configs/world/bimanual_table.yml` 中定义为obstacle
✗ **不要**：把桌子放在robot URDF里

### 4. EE Link的理解
- `ee_link`: 主要末端执行器（通常是第一个臂）
- `link_names`: 所有可作为目标的link列表（可以包含多个臂的EE）
- 使用 `link_poses` 参数可以同时指定多个link的目标

---

## ⚙️ Collision Sphere配置

### 什么是Collision Spheres？

CuRobo使用**球体近似（sphere approximation）**来表示机器人的几何形状，实现超快速的GPU并行碰撞检测。

**工作原理：**
```
URDF链接几何 → Sphere近似 → GPU并行距离计算 → 碰撞检测
```

**优点：**
- ✅ 极快（GPU并行计算）
- ✅ 平滑梯度（用于优化）
- ✅ 适合实时运动规划

**权衡：**
- ⚠️ 可能过于保守（sphere比实际几何大）

### Sphere配置文件结构

```yaml
# robot_description/configs/robot/spheres/bimanual_panda_tesollo.yml
collision_spheres:
  left_panda_link1:
    - center: [0.0, -0.08, 0.0]  # [x, y, z] 相对link原点的偏移（米）
      radius: 0.055               # 球体半径（米）
    - center: [0.0, -0.03, 0.0]
      radius: 0.06
```

### 当前配置来源

**Panda手臂：**
- 基于 `src/curobo/content/configs/robot/spheres/franka_mesh.yml`
- 精确的多球体近似，每个link 3-7个spheres

**Tesollo DG3F手爪：**
- ⚠️ **当前问题**：之前基于robotiq（2指parallel gripper）配置
- ✅ **正确方法**：应该基于Tesollo URDF（3指，每指4关节）

### 为Tesollo手爪生成正确的Spheres

我们提供了工具来基于URDF分析生成sphere配置：

```bash
# 生成sphere配置（基于URDF inertial和joint offsets）
python tools/generate_hand_spheres.py
```

**输出：**
```yaml
# 单臂配置
delto_base_link:
  - center: [0.0, 0.0, 0.0]
    radius: 0.035
  - center: [0.0, 0.0, -0.02]
    radius: 0.035

F1_01:
  - center: [0.0, 0.0, 0.0]
    radius: 0.015

# ... 每个手指link都有sphere定义
```

**Tesollo DG3F结构：**
```
delto_base_link (手掌)
├─ F1_01 → F1_02 → F1_03 → F1_04 → F1_TIP  (手指1)
├─ F2_01 → F2_02 → F2_03 → F2_04 → F2_TIP  (手指2)
└─ F3_01 → F3_02 → F3_03 → F3_04 → F3_TIP  (手指3)
```

### 如何调整Sphere配置

1. **查看当前配置：**
   ```bash
   cat robot_description/configs/robot/spheres/bimanual_panda_tesollo.yml
   ```

2. **基于URDF重新生成：**
   ```bash
   python tools/generate_hand_spheres.py > new_spheres.yml
   ```

3. **手动调整半径：**
   - 增大半径 → 更保守（安全但限制空间）
   - 减小半径 → 更激进（更大工作空间但可能不安全）

4. **可视化验证：**
   ```bash
   python examples/visualize_spheres_official.py
   # 在Isaac Sim或在线viewer中检查sphere是否合理覆盖机器人几何
   ```

### Sphere配置参数

```yaml
# robot_description/configs/robot/bimanual_panda_tesollo.yml
kinematics:
  collision_spheres: 'spheres/bimanual_panda_tesollo.yml'  # Sphere配置文件
  collision_sphere_buffer: 0.004                            # 额外安全距离（米）

  self_collision_ignore:  # 不检查碰撞的link对（如相邻links）
    "left_panda_link1": ["left_panda_link2", "left_panda_link3"]
    # ...
```

---

## 🎨 可视化Collision Spheres

### 官方可视化方法

CuRobo官方网站使用的就是这个方法：

```python
from curobo.util.usd_helper import UsdHelper

UsdHelper.write_trajectory_animation_with_robot_usd(
    robot_cfg="robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
    world_cfg=world_cfg,
    start_state=q_start,
    trajectory=q_trajectory,
    save_path="output.usd",
    visualize_robot_spheres=True,  # ← 关键参数！默认就是True
    base_frame="/world",
)
```

**生成的USD文件包含：**
- Robot meshes（实际外观）
- Collision spheres（半透明蓝绿色球体）
- World obstacles（桌子、障碍物等）

### 快速可视化

我们提供了完整的可视化示例：

```bash
# 1. 静态可视化（推荐）
python examples/visualize_spheres_official.py

# 2. 带动画的可视化（sphere随机器人运动）
python examples/visualize_spheres_official.py motion

# 3. 查看配置统计
python examples/visualize_spheres_official.py stats
```

### 如何查看USD文件

生成的 `.usd` 文件可以用以下方式查看：

#### 方法1: NVIDIA Isaac Sim（最佳）

```bash
# 启动Isaac Sim并打开USD文件
~/.local/share/ov/pkg/isaac-sim-*/isaac-sim.sh bimanual_spheres.usd

# 或在Isaac Sim GUI中:
# File → Open → 选择 bimanual_spheres.usd
```

#### 方法2: 在线USD Viewer（最简单）

1. 访问 https://usd-viewer.glitch.me/
2. 拖拽上传 `.usd` 文件
3. 使用鼠标旋转、缩放、平移查看

**优点：** 无需安装任何软件
**缺点：** 大文件可能加载慢

#### 方法3: usdview（命令行）

```bash
usdview bimanual_spheres.usd
```

**注意：** `usdview` 不是curobo自带的，需要单独安装：
- 它是USD（Universal Scene Description）生态的官方工具
- 由Pixar开发，NVIDIA Omniverse使用
- 安装方法：https://github.com/PixarAnimationStudios/USD

### USD场景结构

打开USD文件后，场景树结构如下：

```
/world/
├── robot/                        # Robot visual meshes
│   ├── left_panda_link0/
│   ├── left_panda_link1/
│   └── ...
├── curobo/
│   └── robot_collision/          # Collision spheres（可切换显示/隐藏）
│       ├── left_panda_link0_0/   # 半透明蓝绿色球体
│       ├── left_panda_link1_0/
│       └── ...
└── world/                        # World obstacles
    └── table/
```

**提示：** 在viewer中可以切换 `/world/curobo/robot_collision/` 的可见性来显示/隐藏collision spheres。

### 在运动规划中自动可视化

运行运动规划示例时，会自动生成包含spheres的USD文件：

```bash
python examples/bimanual_motion_gen_example.py

# 输出：bimanual_trajectory.usd
# 包含：机器人动画 + collision spheres + 桌子
```

打开这个文件可以看到：
- 起始和目标配置
- 规划的轨迹（平滑运动）
- Collision spheres随机器人运动
- 世界障碍物

### 详细可视化指南

完整的可视化教程请参考：
```bash
examples/VISUALIZATION_GUIDE.md
```

包含：
- USD文件结构详解
- 自定义sphere颜色
- 调试可视化技巧
- 常见问题解决

---

## 🎯 三个问题的答案总结

### Q1: 新URDF是否需要包含桌子？
**答**: ❌ **不需要**
桌子应该在world config中定义为obstacle，不是robot的一部分。

### Q2: 桌子是否应该放在world config内？
**答**: ✅ **是的**
已创建 `bimanual_table.yml`，桌子作为cuboid obstacle定义。

### Q3: Config yaml中只有一个ee link？
**答**: `ee_link` 是主EE，但可以通过 `link_names` 定义多个可控制的link。
- `ee_link: "left_delto_base_link"` - 主EE（手掌base）
- `link_names: ["left_delto_base_link", "right_delto_base_link"]` - 双臂EE
- 使用 `link_poses` 参数在planning时同时控制多个link

**配置文件位置**: `robot_description/configs/robot/bimanual_panda_tesollo.yml`

---

## 📊 系统结构

### 双臂位置（参考bimanual_arms.urdf）
```
左臂:  xyz=(-0.558, -0.092, 0.0225), rpy=(0, 0, 0)        [朝前]
右臂:  xyz=(0.5588, -0.092, 0.0225), rpy=(0, 0, 3.14159)  [旋转180°]
桌面:  xyz=(0, 0, 0.9144)
```

### 自由度分布
```
左臂:    7 DoF  (panda arm)
左手爪: 12 DoF  (3 fingers × 4 joints - Tesollo DG3F)
右臂:    7 DoF  (panda arm)
右手爪: 12 DoF  (3 fingers × 4 joints - Tesollo DG3F)
━━━━━━━━━━━━━━━━━━━━━
总计:   38 DoF
```

### Collision Sphere统计
```
左臂Panda:       ~25 spheres (基于franka_mesh.yml)
左手Tesollo:     ~20 spheres (3指 × 多个segments)
右臂Panda:       ~25 spheres
右手Tesollo:     ~20 spheres
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总计:           ~90 spheres
```

---

## 🔄 重新生成URDF

如果需要修改双臂位置关系：

```bash
# 编辑生成脚本
vim robot_description/composites/generate_bimanual_panda_tesollo.py

# 修改位置参数
left_position=(-0.558, -0.092, 0.0225)   # 修改这里
right_position=(0.5588, -0.092, 0.0225)  # 修改这里

# 重新生成URDF
python robot_description/composites/generate_bimanual_panda_tesollo.py
```

---

## 🐛 常见问题

### 1. 规划总是失败
- 检查起始状态是否有碰撞
- 验证目标位姿是否可达
- 增加 `max_attempts`
- 检查障碍物配置
- **可视化collision spheres查看是否有意外碰撞**

### 2. 双臂互相碰撞
- 验证 `self_collision_ignore` 配置
- 增加 `collision_sphere_buffer`
- 检查双臂安装位置
- **可视化spheres检查左右臂是否有重叠**

### 3. 与桌子碰撞
- 检查 `robot_description/configs/world/bimanual_table.yml` 中桌子高度
- 验证臂基座安装高度（URDF中 z=0.0225）
- 确保桌子中心在正确位置（z=0.89175）
- **可视化确认桌子和机器人的相对位置**

### 4. Sphere配置不准确
- ⚠️ **当前问题**：手爪sphere基于robotiq（2指），但Tesollo是3指手
- ✅ **解决方法**：使用 `tools/generate_hand_spheres.py` 重新生成
- 📝 **验证方法**：运行 `visualize_spheres_official.py` 查看sphere是否合理覆盖手指

### 5. USD文件无法查看
- **没有usdview**: 使用Isaac Sim或在线viewer (https://usd-viewer.glitch.me/)
- **文件太大**: 减少轨迹帧数或interpolation_steps
- **加载慢**: 使用 `flatten_usd=True` 参数

---

## 📚 参考资料

### 文档
- 详细英文文档: `examples/BIMANUAL_README.md`
- 可视化指南: `examples/VISUALIZATION_GUIDE.md`
- 配置文件说明: `robot_description/configs/README.md`

### URDF文件
- 单臂URDF: `robot_description/rl/panda_w_tesollo.urdf`
- 双臂URDF: `robot_description/rl/bimanual_panda_tesollo.urdf`
- 参考双臂: `robot_description/ros/bimanual_arms.urdf`

### 配置文件
- Robot config: `robot_description/configs/robot/bimanual_panda_tesollo.yml`
- Sphere config: `robot_description/configs/robot/spheres/bimanual_panda_tesollo.yml`
- World config: `robot_description/configs/world/bimanual_table.yml`

### 示例代码
- 运动规划: `examples/bimanual_motion_gen_example.py`
- Sphere可视化: `examples/visualize_spheres_official.py`
- Isaac Sim多臂: `examples/isaac_sim/multi_arm_reacher.py`
- USD示例: `examples/usd_example.py`

### 工具脚本
- URDF生成器: `robot_description/composites/generate_bimanual_panda_tesollo.py`
- Sphere生成器: `tools/generate_hand_spheres.py`

### 外部资源
- CuRobo官方文档: https://curobo.org/
- USD规范: https://graphics.pixar.com/usd/docs/index.html
- Isaac Sim: https://developer.nvidia.com/isaac-sim

---

## ✅ 验证安装

```bash
# 运行验证脚本
python -c "
from pathlib import Path

files = [
    # URDF
    'robot_description/rl/bimanual_panda_tesollo.urdf',

    # 配置
    'robot_description/configs/robot/bimanual_panda_tesollo.yml',
    'robot_description/configs/robot/spheres/bimanual_panda_tesollo.yml',
    'robot_description/configs/world/bimanual_table.yml',

    # 示例
    'examples/bimanual_motion_gen_example.py',
    'examples/visualize_spheres_official.py',

    # 工具
    'tools/generate_hand_spheres.py',

    # 文档
    'examples/BIMANUAL_README.md',
    'examples/VISUALIZATION_GUIDE.md',
]

print('=' * 60)
print('File Verification')
print('=' * 60)
for f in files:
    status = '✓' if Path(f).exists() else '✗'
    print(f'{status} {f}')
print('=' * 60)
"
```

---

## 🚀 下一步

1. ✅ 运行运动规划示例
   ```bash
   python examples/bimanual_motion_gen_example.py
   ```

2. ✅ 可视化collision spheres
   ```bash
   python examples/visualize_spheres_official.py
   ```

3. ✅ 在Isaac Sim或在线viewer中查看生成的USD文件

4. ✅ 根据实际需求调整sphere配置
   ```bash
   python tools/generate_hand_spheres.py
   ```

5. ✅ 开始开发你的双臂应用！

---

**创建时间**: 2026-02-14
**最后更新**: 2026-02-15
**版本**: 2.0
**包含**: URDF生成器 + 配置文件 + Sphere工具 + 可视化示例 + 完整文档
