# CuRobo Collision Sphere Visualization Guide

## 🎯 Overview

CuRobo uses **sphere approximations** for fast GPU-accelerated collision detection. This guide shows you how to visualize these collision spheres.

## 📊 What You'll See

When you visualize collision spheres, you'll see:
- **Robot mesh** (actual visual appearance)
- **Collision spheres** (semi-transparent cyan/blue-green spheres)
- **World obstacles** (tables, boxes, etc.)

The spheres approximate the robot's geometry for fast collision checking.

## 🚀 Quick Start

### Method 1: Static Visualization (Recommended)

```bash
# Generate USD file with collision spheres
python examples/visualize_spheres_official.py

# Output: bimanual_spheres.usd
```

### Method 2: Animated Visualization

```bash
# Generate animated USD (spheres move with robot)
python examples/visualize_spheres_official.py motion

# Output: bimanual_motion_spheres.usd
```

### Method 3: Configuration Statistics

```bash
# Print sphere configuration stats
python examples/visualize_spheres_official.py stats
```

## 👀 How to View USD Files

CuRobo generates `.usd` (Universal Scene Description) files. Here's how to view them:

### Option A: NVIDIA Isaac Sim (Best)

If you have Isaac Sim installed:
```bash
# Launch Isaac Sim and open the USD file
~/.local/share/ov/pkg/isaac-sim-*/isaac-sim.sh bimanual_spheres.usd

# Or from Isaac Sim GUI:
# File → Open → Select bimanual_spheres.usd
```

### Option B: Online USD Viewer

1. Go to https://usd-viewer.glitch.me/
2. Drag and drop your `.usd` file
3. Navigate with mouse (rotate, pan, zoom)

**Note**: Large files may take time to load.

### Option C: usdview (Command Line)

If you have USD tools installed:
```bash
usdview bimanual_spheres.usd
```

**Installing usdview** (optional, requires building USD from source):
- https://github.com/PixarAnimationStudios/USD
- Pre-built packages: Check NVIDIA Omniverse

### Option D: Python (Read USD Structure)

```python
from pxr import Usd

stage = Usd.Stage.Open("bimanual_spheres.usd")
print(stage.ExportToString())
```

## 📂 USD Scene Structure

When you open the USD file, you'll see this hierarchy:

```
/world/
├── robot/                      # Robot visual meshes
│   ├── left_panda_link0/
│   ├── left_panda_link1/
│   └── ...
├── curobo/
│   └── robot_collision/        # Collision spheres (toggle visibility)
│       ├── left_panda_link0_0/
│       ├── left_panda_link1_0/
│       └── ...
└── world/                      # World obstacles
    └── table/
```

**Tip**: Toggle visibility of `/world/curobo/robot_collision/` to show/hide spheres.

## 🔧 Official CuRobo Method

The visualization uses CuRobo's built-in USD export:

```python
from curobo.util.usd_helper import UsdHelper

UsdHelper.write_trajectory_animation_with_robot_usd(
    robot_cfg="robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
    world_model=world_cfg,
    start_state=q_start,
    trajectory=q_trajectory,
    save_path="output.usd",
    visualize_robot_spheres=True,  # ← This enables sphere visualization!
    base_frame="/world",
)
```

This is the **same method used on CuRobo's official website** to generate visualizations.

## 📝 Key Parameters

- `visualize_robot_spheres=True` - Enable sphere visualization (default)
- `robot_color=[R, G, B, A]` - Change robot color (RGBA, 0-1 range)
- `interpolation_steps` - Animation interpolation smoothness
- `dt` - Time step for animation (e.g., 1/60 for 60 FPS)

## 🎨 Customizing Sphere Colors

By default, spheres are semi-transparent cyan. To change:

```python
# In src/curobo/util/usd_helper.py line ~1004:
for s in sphere_traj:
    for k in s:
        k.color = [0, 0.27, 0.27, 1.0]  # Change this [R, G, B, A]
```

Common colors:
- Cyan: `[0, 0.27, 0.27, 1.0]` (default)
- Red: `[1.0, 0, 0, 0.5]`
- Green: `[0, 1.0, 0, 0.5]`
- Blue: `[0, 0, 1.0, 0.5]`

## 🔍 Understanding Sphere Configurations

### Where Spheres Are Defined

```bash
robot_description/configs/robot/spheres/bimanual_panda_tesollo.yml
```

### Format

```yaml
collision_spheres:
  left_panda_link1:
    - center: [0.0, -0.08, 0.0]
      radius: 0.055
    - center: [0.0, -0.03, 0.0]
      radius: 0.06
```

- `center`: [x, y, z] offset from link origin (meters)
- `radius`: Sphere radius (meters)

### How Spheres Are Generated

1. **From URDF**: Analyze link dimensions, inertial properties
2. **From Mesh**: Compute bounding boxes/convex hulls
3. **Manual tuning**: Adjust for better coverage vs. conservativeness

See `tools/generate_hand_spheres.py` for how we generated Tesollo hand spheres.

## 📊 Visualization in Motion Planning

When you run motion planning examples, USD output automatically includes spheres:

```bash
python examples/bimanual_motion_gen_example.py

# Output: bimanual_trajectory.usd
# Contains: robot animation + collision spheres + obstacles
```

Open the generated USD to see:
- Start and goal configurations
- Planned trajectory (smooth motion)
- Collision spheres moving with robot
- World obstacles (table, boxes, etc.)

## 🐛 Troubleshooting

### "No viewer available"

- **Solution**: Use online viewer or Isaac Sim
- **Quick check**: `ls -lh *.usd` to verify file was created

### "Spheres not visible"

1. Check USD scene tree for `/world/curobo/robot_collision/`
2. Toggle layer visibility in viewer
3. Verify `visualize_robot_spheres=True` in your code

### "USD file too large"

- Reduce `interpolation_steps`
- Use fewer trajectory frames
- Simplify sphere configuration (fewer spheres per link)

## 📚 References

- **CuRobo Documentation**: https://curobo.org/
- **USD Documentation**: https://graphics.pixar.com/usd/docs/index.html
- **Isaac Sim**: https://developer.nvidia.com/isaac-sim
- **Example Code**: `examples/usd_example.py` (official CuRobo examples)

## 🎓 Next Steps

1. ✅ Generate static sphere visualization
2. ✅ View in Isaac Sim or online viewer
3. ✅ Run motion planning and visualize trajectories
4. ✅ Adjust sphere configurations for your robot
5. ✅ Fine-tune collision checking parameters

---

**Created for**: Bimanual Panda + Tesollo DG3F system
**Based on**: CuRobo official visualization methods
