"""
Visualize collision spheres using CuRobo's official USD methods.

This script demonstrates the official way to visualize collision spheres
as shown on CuRobo's website and documentation.
"""

import torch
from curobo.geom.types import WorldConfig
from curobo.types.base import TensorDeviceType
from curobo.types.robot import JointState
from curobo.util.usd_helper import UsdHelper
from curobo.util_file import get_robot_configs_path, join_path, load_yaml


def visualize_spheres_static(
    robot_file: str = "robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
    world_file: str = "robot/robot_description/configs/world/bimanual_table.yml",
    output_file: str = "bimanual_spheres.usd",
):
    """
    Official method 1: Static robot with collision spheres.

    This uses UsdHelper.write_trajectory_animation_with_robot_usd()
    with visualize_robot_spheres=True (default).
    """

    print("=" * 80)
    print("CuRobo Official Sphere Visualization")
    print("=" * 80)

    # Setup
    tensor_args = TensorDeviceType(device=torch.device("cuda:0"))

    # Load configurations
    print("\n[1/4] Loading robot configuration...")
    robot_cfg = load_yaml(join_path(get_robot_configs_path(), robot_file))

    print("[2/4] Loading world configuration...")
    world_cfg = WorldConfig.from_dict(
        load_yaml(join_path(get_robot_configs_path(), world_file))
    )

    # Get retract configuration
    print("[3/4] Preparing robot state...")
    retract_config = robot_cfg["robot_cfg"]["kinematics"]["cspace"]["retract_config"]
    q_position = torch.tensor(
        [retract_config], device=tensor_args.device, dtype=tensor_args.dtype
    )
    q_start = JointState.from_position(q_position)

    # Create USD with spheres
    print("[4/4] Generating USD file with collision spheres...")

    # Official method - this is what CuRobo uses internally
    UsdHelper.write_trajectory_animation_with_robot_usd(
        robot_cfg=robot_file,
        world_model=world_cfg,
        start_state=q_start,
        trajectory=q_start,  # Single frame
        dt=0.02,
        save_path=output_file,
        base_frame="/world",
        visualize_robot_spheres=True,  # This is the key parameter!
        robot_color=[0.8, 0.8, 0.8, 1.0],  # Light gray robot
        interpolation_steps=1,
    )

    print(f"\n{'='*80}")
    print(f"✓ Visualization saved: {output_file}")
    print(f"{'='*80}")
    print(f"\nTo view the USD file:")
    print(f"  1. Isaac Sim: Open {output_file}")
    print(f"  2. Online: Upload to https://usd-viewer.glitch.me/")
    print(f"  3. usdview: usdview {output_file} (if installed)")
    print(f"\nIn the USD scene:")
    print(f"  - Robot meshes: /world/robot/...")
    print(f"  - Collision spheres: /world/curobo/robot_collision/...")
    print(f"    (Semi-transparent cyan spheres)")
    print(f"  - World obstacles: /world/world/...")


def visualize_spheres_with_motion(
    robot_file: str = "robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
    world_file: str = "robot/robot_description/configs/world/bimanual_table.yml",
    output_file: str = "bimanual_motion_spheres.usd",
):
    """
    Official method 2: Animated robot with collision spheres.

    Shows how spheres move with the robot during motion.
    """

    print("=" * 80)
    print("CuRobo Official Motion + Spheres Visualization")
    print("=" * 80)

    # Setup
    tensor_args = TensorDeviceType(device=torch.device("cuda:0"))

    # Load configurations
    print("\n[1/5] Loading configurations...")
    robot_cfg = load_yaml(join_path(get_robot_configs_path(), robot_file))
    world_cfg = WorldConfig.from_dict(
        load_yaml(join_path(get_robot_configs_path(), world_file))
    )

    # Create a simple motion: interpolate between two configurations
    print("[2/5] Creating simple motion...")
    retract_config = robot_cfg["robot_cfg"]["kinematics"]["cspace"]["retract_config"]
    n_dof = len(retract_config)
    n_frames = 60  # 1 second at 60fps

    # Start: retract config
    q_start = torch.tensor(retract_config, device=tensor_args.device, dtype=tensor_args.dtype)

    # End: move some joints
    q_end = q_start.clone()
    q_end[:7] = q_end[:7] + torch.tensor(
        [0.3, -0.2, 0.2, -0.3, 0.2, 0.3, 0.0],
        device=tensor_args.device,
        dtype=tensor_args.dtype
    )

    # Interpolate
    alpha = torch.linspace(0, 1, n_frames, device=tensor_args.device, dtype=tensor_args.dtype)
    trajectory = q_start.unsqueeze(0) + alpha.unsqueeze(1) * (q_end - q_start).unsqueeze(0)

    print(f"[3/5] Generated trajectory with {n_frames} frames")

    # Create USD with animated spheres
    print("[4/5] Generating USD file...")

    q_start_state = JointState.from_position(q_start.unsqueeze(0))
    q_trajectory = JointState.from_position(trajectory)

    UsdHelper.write_trajectory_animation_with_robot_usd(
        robot_cfg=robot_file,
        world_model=world_cfg,
        start_state=q_start_state,
        trajectory=q_trajectory,
        dt=1.0/60.0,  # 60 FPS
        save_path=output_file,
        base_frame="/world",
        visualize_robot_spheres=True,  # Spheres animate with robot!
        robot_color=[0.7, 0.9, 0.7, 1.0],  # Light green
        interpolation_steps=1,
    )

    print(f"\n{'='*80}")
    print(f"✓ Animated visualization saved: {output_file}")
    print(f"{'='*80}")
    print(f"\nThis USD contains:")
    print(f"  - {n_frames} frames of animation")
    print(f"  - Robot mesh animated")
    print(f"  - Collision spheres animated (move with robot)")
    print(f"\nUse Isaac Sim or compatible USD viewer to play the animation.")


def compare_sphere_configs():
    """
    Helper: Print sphere configuration statistics.
    """

    print("=" * 80)
    print("Collision Sphere Configuration Analysis")
    print("=" * 80)

    robot_file = "robot/robot_description/configs/robot/bimanual_panda_tesollo.yml"
    robot_cfg = load_yaml(join_path(get_robot_configs_path(), robot_file))

    # Load sphere config
    sphere_file = robot_cfg["robot_cfg"]["kinematics"]["collision_spheres"]
    sphere_cfg = load_yaml(join_path(get_robot_configs_path(), sphere_file))

    collision_spheres = sphere_cfg.get("collision_spheres", {})

    print(f"\nTotal collision links: {len(collision_spheres)}")

    total_spheres = sum(len(spheres) for spheres in collision_spheres.values())
    print(f"Total collision spheres: {total_spheres}")

    # Group by arm/hand
    left_links = [k for k in collision_spheres.keys() if k.startswith("left_")]
    right_links = [k for k in collision_spheres.keys() if k.startswith("right_")]

    left_spheres = sum(len(collision_spheres[k]) for k in left_links)
    right_spheres = sum(len(collision_spheres[k]) for k in right_links)

    print(f"\nLeft arm:")
    print(f"  Links: {len(left_links)}")
    print(f"  Spheres: {left_spheres}")

    print(f"\nRight arm:")
    print(f"  Links: {len(right_links)}")
    print(f"  Spheres: {right_spheres}")

    # Show sample links
    print(f"\nSample links (first 5):")
    for i, (link_name, spheres) in enumerate(list(collision_spheres.items())[:5]):
        print(f"  {link_name}: {len(spheres)} spheres")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "motion":
        # Animated visualization
        visualize_spheres_with_motion()
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        # Just print statistics
        compare_sphere_configs()
    else:
        # Static visualization (default)
        visualize_spheres_static()
        print("\n" + "="*80)
        print("Tip: Run with 'motion' argument for animated visualization:")
        print("  python examples/visualize_spheres_official.py motion")
        print("="*80)
