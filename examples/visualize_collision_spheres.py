"""
Visualize collision spheres for bimanual Panda robot.
Shows the sphere approximation used for collision detection.
"""

import torch
from curobo.cuda_robot_model.cuda_robot_model import CudaRobotModel, CudaRobotModelConfig
from curobo.geom.types import WorldConfig
from curobo.types.base import TensorDeviceType
from curobo.types.robot import JointState
from curobo.util.usd_helper import UsdHelper
from curobo.util_file import get_robot_configs_path, join_path, load_yaml


def visualize_spheres():
    """Visualize collision spheres for the bimanual robot."""

    print("=" * 80)
    print("Collision Sphere Visualization")
    print("=" * 80)

    # Setup
    tensor_args = TensorDeviceType(device=torch.device("cuda:0"))

    # Load robot configuration
    print("\n[1/4] Loading robot configuration...")
    robot_cfg_file = "robot/robot_description/configs/robot/bimanual_panda_tesollo.yml"
    world_cfg_file = "robot/robot_description/configs/world/bimanual_table.yml"

    config_file = load_yaml(join_path(get_robot_configs_path(), robot_cfg_file))
    config_file["robot_cfg"]["kinematics"]["load_link_names_with_mesh"] = True

    robot_cfg = CudaRobotModelConfig.from_data_dict(
        config_file["robot_cfg"]["kinematics"],
        tensor_args=tensor_args
    )

    # Create robot model
    print("[2/4] Creating robot model...")
    kin_model = CudaRobotModel(robot_cfg)

    # Load world configuration
    print("[3/4] Loading world configuration...")
    world_cfg = WorldConfig.from_dict(
        load_yaml(join_path(get_robot_configs_path(), world_cfg_file))
    )

    # Get retract configuration (home position)
    retract_cfg = config_file["robot_cfg"]["kinematics"]["cspace"]["retract_config"]
    q_position = torch.tensor([retract_cfg], device=tensor_args.device, dtype=tensor_args.dtype)
    q_start = JointState.from_position(q_position)

    # Get collision spheres at retract position
    print("[4/4] Generating visualization...")
    sphere_model = kin_model.get_robot_as_spheres(q_start.position)

    # Print sphere statistics
    total_spheres = sum(len(link_spheres) for link_spheres in sphere_model[0])
    print(f"\nRobot Configuration:")
    print(f"  Total DoF: {len(retract_cfg)}")
    print(f"  Total collision spheres: {total_spheres}")
    print(f"  Collision links: {len(sphere_model[0])}")

    # Create USD file
    output_file = "collision_spheres.usd"
    usd_helper = UsdHelper()
    usd_helper.create_stage(output_file, timesteps=1, dt=0.02, base_frame="/world")

    # Add world obstacles
    usd_helper.add_world_to_stage(world_cfg, base_frame="/world")

    # Add robot meshes (for reference)
    robot_meshes = kin_model.get_robot_link_meshes()
    robot_mesh_model = WorldConfig(mesh=robot_meshes)

    animation_links = kin_model.kinematics_config.mesh_link_names
    animation_poses = kin_model.get_link_poses(q_start.position.contiguous(), animation_links)

    usd_helper.create_animation(
        robot_mesh_model,
        animation_poses,
        "/world",
        robot_frame="/world/robot"
    )

    # Add collision spheres (semi-transparent blue-green)
    for sphere_list in sphere_model:
        for sphere in sphere_list:
            sphere.color = [0, 0.27, 0.27, 0.5]  # Semi-transparent cyan

    usd_helper.create_obstacle_animation(
        sphere_model,
        base_frame="/world",
        obstacles_frame="curobo/collision_spheres"
    )

    # Save USD file
    usd_helper.write_stage_to_file(output_file)

    print(f"\n{'='*80}")
    print(f"✓ Visualization saved to: {output_file}")
    print(f"{'='*80}")
    print(f"\nTo view:")
    print(f"  usdview {output_file}")
    print(f"\nIn USD viewer:")
    print(f"  - Robot meshes: /world/robot/...")
    print(f"  - Collision spheres: /world/curobo/collision_spheres/...")
    print(f"  - Table: /world/world/table")
    print(f"\nYou can toggle visibility of collision spheres in the scene hierarchy.")


if __name__ == "__main__":
    visualize_spheres()
