# Bimanual Panda with Tesollo Gripper - Motion Generation

This directory contains everything needed to use cuRobo for dual-arm motion planning with Tesollo DG3F grippers.

## 📁 Generated Files

### 1. URDF Generation Script
**Location**: `robot_description/composites/generate_bimanual_panda_tesollo.py`

Python script that generates the bimanual URDF from the single-arm version.

```bash
# Regenerate the bimanual URDF if needed:
python robot_description/composites/generate_bimanual_panda_tesollo.py
```

### 2. Robot URDF
**Location**: `robot_description/rl/bimanual_panda_tesollo.urdf`

Generated bimanual URDF containing:
- Left arm: Panda (7 DoF) + Tesollo DG3F gripper (12 DoF)
- Right arm: Panda (7 DoF) + Tesollo DG3F gripper (12 DoF)
- Total: 38 DoF
- **Note**: Does NOT include table (table is in world config)

### 3. Robot Configuration
**Location**: `robot_description/configs/robot/bimanual_panda_tesollo.yml`

CuRobo robot configuration including:
- Kinematic structure
- Joint names and limits
- Collision checking setup
- Self-collision pairs
- Multiple end-effector links

**Key parameters**:
- `base_link`: "world"
- `ee_link`: "left_F1_TIP_TOP" (primary EE)
- `link_names`: ["left_F1_TIP_TOP", "right_F1_TIP_TOP"] (both EEs)

### 4. Collision Spheres
**Location**: `robot_description/configs/robot/spheres/bimanual_panda_tesollo.yml`

Simplified sphere representation for fast collision checking.

### 5. World Configuration
**Location**: `robot_description/configs/world/bimanual_table.yml`

World obstacles including the work table:
- Dimensions: 1.8288m × 0.62865m × 0.045m
- Position: Matches the mounting positions in the URDF

### 6. Example Code
**Location**: `examples/bimanual_motion_gen_example.py`

Demonstration of bimanual motion planning with collision avoidance.

## 🚀 Quick Start

### Basic Usage

```python
import torch
from curobo.types.base import TensorDeviceType
from curobo.types.math import Pose
from curobo.types.robot import JointState
from curobo.wrap.reacher.motion_gen import MotionGen, MotionGenConfig

# Setup
tensor_args = TensorDeviceType(device=torch.device("cuda:0"))

# Load configuration
motion_gen_cfg = MotionGenConfig.load_from_robot_config(
    robot_cfg="robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
    world_cfg="robot/robot_description/configs/world/bimanual_table.yml",
    tensor_args=tensor_args,
)

motion_gen = MotionGen(motion_gen_cfg)
motion_gen.warmup()

# Define start configuration (38 DoF)
q_start = JointState.from_position(
    tensor_args.to_device([[
        # Left arm (7 joints)
        0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785,
        # Left gripper (12 joints)
        0.0, 0.0, 0.0, 0.0,  # Finger 1
        0.0, 0.0, 0.0, 0.0,  # Finger 2
        0.0, 0.0, 0.0, 0.0,  # Finger 3
        # Right arm (7 joints)
        0.0, -0.785, 0.0, -2.356, 0.0, 1.571, -0.785,
        # Right gripper (12 joints)
        0.0, 0.0, 0.0, 0.0,  # Finger 1
        0.0, 0.0, 0.0, 0.0,  # Finger 2
        0.0, 0.0, 0.0, 0.0,  # Finger 3
    ]]),
    joint_names=[
        'left_panda_joint1', 'left_panda_joint2', 'left_panda_joint3', 'left_panda_joint4',
        'left_panda_joint5', 'left_panda_joint6', 'left_panda_joint7',
        'left_F1M1', 'left_F1M2', 'left_F1M3', 'left_F1M4',
        'left_F2M1', 'left_F2M2', 'left_F2M3', 'left_F2M4',
        'left_F3M1', 'left_F3M2', 'left_F3M3', 'left_F3M4',
        'right_panda_joint1', 'right_panda_joint2', 'right_panda_joint3', 'right_panda_joint4',
        'right_panda_joint5', 'right_panda_joint6', 'right_panda_joint7',
        'right_F1M1', 'right_F1M2', 'right_F1M3', 'right_F1M4',
        'right_F2M1', 'right_F2M2', 'right_F2M3', 'right_F2M4',
        'right_F3M1', 'right_F3M2', 'right_F3M3', 'right_F3M4',
    ],
)

# Define goal for left arm (primary EE)
left_goal = Pose(
    position=tensor_args.to_device([[0.5, 0.3, 1.0]]),
    quaternion=tensor_args.to_device([[1, 0, 0, 0]]),
)

# Define goal for right arm (using link_poses)
link_poses = {
    "right_F1_TIP_TOP": Pose(
        position=tensor_args.to_device([[0.5, -0.3, 1.0]]),
        quaternion=tensor_args.to_device([[1, 0, 0, 0]]),
    )
}

# Plan trajectory
result = motion_gen.plan_single(
    q_start,
    left_goal,
    link_poses=link_poses
)

if result.success.item():
    trajectory = result.get_interpolated_plan()
    print(f"Success! Trajectory has {len(trajectory.position)} steps")
else:
    print(f"Planning failed: {result.status}")
```

### Run Example

```bash
# Basic bimanual motion planning
python examples/bimanual_motion_gen_example.py
```

## 🏗️ System Architecture

### Coordinate Frames

```
world (base_link)
├── left_panda_link0
│   └── ... (7 Panda links)
│       └── left_panda_link8
│           └── left_delto_base_link
│               ├── left_F1_* (Finger 1)
│               │   └── left_F1_TIP_TOP
│               ├── left_F2_* (Finger 2)
│               │   └── left_F2_TIP_TOP
│               └── left_F3_* (Finger 3)
│                   └── left_F3_TIP_TOP
└── right_panda_link0
    └── ... (mirrored structure)
```

### Arm Mounting Positions

Based on `bimanual_arms.urdf.xacro`:

- **Left arm**:
  - Position: `xyz=(-0.558, -0.092, 0.0225)`
  - Rotation: `rpy=(0, 0, 0)` (facing forward)

- **Right arm**:
  - Position: `xyz=(0.5588, -0.092, 0.0225)`
  - Rotation: `rpy=(0, 0, 3.14159)` (rotated 180° around z-axis)

### Degrees of Freedom

| Component | DoF | Joints |
|-----------|-----|--------|
| Left Panda Arm | 7 | left_panda_joint1-7 |
| Left Tesollo Gripper | 12 | left_F{1,2,3}M{1,2,3,4} |
| Right Panda Arm | 7 | right_panda_joint1-7 |
| Right Tesollo Gripper | 12 | right_F{1,2,3}M{1,2,3,4} |
| **Total** | **38** | |

## 🎯 Key Features

### 1. Dual-Arm Coordination
Control both arms simultaneously with coordinated motion planning.

### 2. Multi-Link Goals
Specify target poses for multiple end-effectors using `link_poses` parameter:

```python
result = motion_gen.plan_single(
    start_state,
    primary_goal,  # Left arm goal
    link_poses={
        "right_F1_TIP_TOP": right_goal,  # Right arm goal
        # Can add more links if needed
    }
)
```

### 3. Collision Avoidance
- **Inter-arm collision**: Automatic avoidance between left and right arms
- **Self-collision**: Each arm avoids self-collision
- **World obstacles**: Table and custom obstacles

### 4. Gripper Control
Each gripper has 3 fingers with 4 joints each:
- F1M1-F1M4: Finger 1
- F2M1-F2M4: Finger 2
- F3M1-F3M4: Finger 3

## 🛠️ Customization

### Add Custom Obstacles

```python
from curobo.geom.types import Cuboid, WorldConfig

# Create custom obstacles
cuboids = [
    Cuboid(name="box1", pose=[0.3, 0, 1.0, 1, 0, 0, 0], dims=[0.1, 0.1, 0.2]),
]

world = WorldConfig(cuboid=cuboids)
motion_gen.update_world(world)
```

### Modify Arm Positions

Edit `robot_description/composites/generate_bimanual_panda_tesollo.py`:

```python
create_bimanual_urdf(
    single_arm_urdf_path=single_arm_urdf,
    output_path=output_urdf,
    left_position=(-0.558, -0.092, 0.0225),   # Modify these
    right_position=(0.5588, -0.092, 0.0225)   # values
)
```

Then regenerate the URDF:
```bash
python robot_description/composites/generate_bimanual_panda_tesollo.py
```

### Tune Planning Parameters

Edit `robot_description/configs/robot/bimanual_panda_tesollo.yml`:

```yaml
cspace:
  max_jerk: 500.0           # Adjust for smoother/faster motion
  max_acceleration: 15.0
  null_space_weight: [...]  # Adjust joint preferences
```

## 📊 Performance Tips

1. **Start with retract config**: Use `motion_gen.get_retract_config()` for reliable starting positions

2. **Adjust collision buffer**: Decrease for tight spaces, increase for safety
   ```python
   collision_activation_distance = 0.025  # Default
   ```

3. **Increase planning attempts**: For difficult scenarios
   ```python
   plan_config = MotionGenPlanConfig(max_attempts=20)
   ```

4. **Use CUDA graphs**: For faster repeated planning
   ```python
   motion_gen_cfg = MotionGenConfig.load_from_robot_config(
       ...,
       use_cuda_graph=True,
   )
   ```

## 🐛 Troubleshooting

### Planning Always Fails
- Check if start state is collision-free
- Verify goal poses are reachable
- Increase `max_attempts` in plan config
- Check if obstacles are properly configured

### Arms Collide with Each Other
- Verify self-collision pairs in robot config
- Increase collision sphere buffer
- Check arm mounting positions

### Table Collision Issues
- Verify table height in `robot_description/configs/world/bimanual_table.yml`
- Check arm base mounting height (z=0.0225 in URDF)
- Ensure table center is at z=0.89175

## 📚 References

- **Single-arm URDF**: `robot_description/rl/panda_w_tesollo.urdf`
- **Reference dual-arm**: `robot_description/ros/bimanual_arms.urdf`
- **CuRobo docs**: https://curobo.org/
- **Isaac Sim example**: `examples/isaac_sim/multi_arm_reacher.py`

## 📝 File Summary

```
curobo-HAND/
├── robot_description/
│   ├── composites/
│   │   └── generate_bimanual_panda_tesollo.py   [URDF generator script]
│   ├── rl/
│   │   ├── panda_w_tesollo.urdf                  [Single-arm source]
│   │   └── bimanual_panda_tesollo.urdf           [Generated dual-arm]
│   └── configs/
│       ├── robot/
│       │   ├── bimanual_panda_tesollo.yml        [Robot config]
│       │   └── spheres/
│       │       └── bimanual_panda_tesollo.yml    [Collision spheres]
│       └── world/
│           └── bimanual_table.yml                [World config]
└── examples/
    ├── bimanual_motion_gen_example.py            [Example code]
    └── BIMANUAL_README.md                        [This file]
```

---

**Generated by**: `generate_bimanual_panda_tesollo.py`
**Last updated**: 2026-02-14
