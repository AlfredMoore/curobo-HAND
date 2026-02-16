#!/usr/bin/env python3
"""
Bimanual Panda with Tesollo Gripper Motion Generation Example

This example demonstrates how to use cuRobo to generate collision-free trajectories
for a dual-arm system with Tesollo DG3F grippers.

Key features:
- Dual arm coordination
- Collision avoidance between arms
- Table obstacle avoidance
- Multi-link target poses (both end-effectors)
"""

import torch
import numpy as np

from curobo.geom.types import Cuboid, WorldConfig
from curobo.types.base import TensorDeviceType
from curobo.types.math import Pose
from curobo.types.robot import JointState
from curobo.util.usd_helper import UsdHelper
from curobo.wrap.reacher.motion_gen import MotionGen, MotionGenConfig, MotionGenPlanConfig


def demo_bimanual_motion_gen():
    """Demonstrate bimanual motion generation with collision avoidance."""

    # Initialize tensor device
    tensor_args = TensorDeviceType(device=torch.device("cuda:0"))

    # Motion generation parameters
    interpolation_dt = 0.02
    collision_activation_distance = 0.025

    print("=" * 80)
    print("Bimanual Panda with Tesollo Gripper - Motion Generation Demo")
    print("=" * 80)

    # Create motion generator configuration
    print("\n[1/6] Loading motion generator configuration...")
    motion_gen_cfg = MotionGenConfig.load_from_robot_config(
        robot_cfg="robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
        world_cfg="robot/robot_description/configs/world/bimanual_table.yml",
        tensor_args=tensor_args,
        trajopt_tsteps=34,
        interpolation_steps=2000,
        num_ik_seeds=30,
        num_trajopt_seeds=4,
        grad_trajopt_iters=500,
        interpolation_dt=interpolation_dt,
        collision_activation_distance=collision_activation_distance,
        evaluate_interpolated_trajectory=True,
    )

    # Create motion generator instance
    motion_gen = MotionGen(motion_gen_cfg)
    print("✓ Motion generator loaded")

    # Warmup (compile CUDA kernels)
    print("\n[2/6] Warming up motion generator (compiling CUDA kernels)...")
    motion_gen.warmup()
    print("✓ Warmup complete")

    # Clear collision cache and reset
    print("\n[3/6] Setting up world...")
    motion_gen.world_coll_checker.clear_cache()
    motion_gen.reset(reset_seed=False)
    print("✓ World setup complete (table loaded from config)")

    # Define start configuration
    # Total DoF: 38 (2 arms × (7 arm joints + 12 gripper joints))
    print("\n[4/6] Setting start configuration...")

    # Start joint positions: retract configuration
    q_start = JointState.from_position(
        tensor_args.to_device([[
            # Left arm - neutral pose
            0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785,
            # Left gripper - open
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            # Right arm - neutral pose (mirrored)
            0.0, -0.785, 0.0, -2.356, 0.0, 1.571, -0.785,
            # Right gripper - open
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
        ]]),
        joint_names=[
            # Left arm
            'left_panda_joint1', 'left_panda_joint2', 'left_panda_joint3', 'left_panda_joint4',
            'left_panda_joint5', 'left_panda_joint6', 'left_panda_joint7',
            # Left gripper
            'left_F1M1', 'left_F1M2', 'left_F1M3', 'left_F1M4',
            'left_F2M1', 'left_F2M2', 'left_F2M3', 'left_F2M4',
            'left_F3M1', 'left_F3M2', 'left_F3M3', 'left_F3M4',
            # Right arm
            'right_panda_joint1', 'right_panda_joint2', 'right_panda_joint3', 'right_panda_joint4',
            'right_panda_joint5', 'right_panda_joint6', 'right_panda_joint7',
            # Right gripper
            'right_F1M1', 'right_F1M2', 'right_F1M3', 'right_F1M4',
            'right_F2M1', 'right_F2M2', 'right_F2M3', 'right_F2M4',
            'right_F3M1', 'right_F3M2', 'right_F3M3', 'right_F3M4',
        ],
    )
    print("✓ Start configuration set")

    # Define goal poses for both end-effectors
    print("\n[5/6] Planning trajectory to goal poses...")

    # Primary goal (left arm end-effector)
    # Position: slightly forward and to the left
    left_ee_goal = Pose(
        position=tensor_args.to_device([[0.3, 0.3, 1.0]]),  # x, y, z
        quaternion=tensor_args.to_device([[1, 0, 0, 0]]),    # w, x, y, z (identity rotation)
    )

    # Secondary goal (right arm end-effector) using link_poses
    # Position: slightly forward and to the right
    link_poses = {
        "right_F1_TIP_TOP": Pose(
            position=tensor_args.to_device([[0.3, -0.3, 1.0]]),  # x, y, z
            quaternion=tensor_args.to_device([[1, 0, 0, 0]]),     # w, x, y, z
        )
    }

    # Create plan configuration
    plan_config = MotionGenPlanConfig(
        enable_graph=False,
        enable_graph_attempt=3,
        max_attempts=10,
        timeout=10.0,
    )

    # Plan motion
    print("  Planning with dual-arm coordination...")
    result = motion_gen.plan_single(
        q_start,
        left_ee_goal,
        plan_config,
        link_poses=link_poses,  # Specify right arm goal
    )

    # Check result
    if result.success.item():
        print("✓ Motion planning SUCCESSFUL!")

        # Get interpolated trajectory
        interpolated_solution = result.get_interpolated_plan()

        print(f"\n[6/6] Trajectory details:")
        print(f"  - Trajectory steps: {len(interpolated_solution.position)}")
        print(f"  - Time step (dt): {result.interpolation_dt:.4f} seconds")
        print(f"  - Total duration: {len(interpolated_solution.position) * result.interpolation_dt:.2f} seconds")
        print(f"  - DoF: {interpolated_solution.position.shape[-1]}")

        # Save trajectory visualization
        output_file = "bimanual_trajectory.usd"
        print(f"\n[Optional] Saving USD animation to: {output_file}")

        # Get world configuration for visualization
        world_cfg = WorldConfig.from_dict({
            'cuboid': {
                'table': {
                    'dims': [1.8288, 0.62865, 0.045],
                    'pose': [0.0, 0.0, 0.89175, 1, 0, 0, 0]
                }
            }
        })

        try:
            UsdHelper.write_trajectory_animation_with_robot_usd(
                robot_cfg="robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
                world_cfg=world_cfg,
                start_state=q_start,
                trajectory=interpolated_solution,
                dt=result.interpolation_dt,
                save_path=output_file,
                base_frame="/world",
                interpolation_steps=1,
            )
            print(f"✓ USD file saved successfully!")
            print(f"  You can view it with: usdview {output_file}")
        except Exception as e:
            print(f"⚠ Could not save USD file: {e}")
            print(f"  (This is optional - trajectory planning was successful)")

        # Print some trajectory statistics
        print(f"\n" + "=" * 80)
        print("Trajectory Summary:")
        print("=" * 80)

        # Get final joint positions
        final_pos = interpolated_solution.position[-1].cpu().numpy()

        print(f"\nFinal joint positions:")
        print(f"  Left arm: {final_pos[:7]}")
        print(f"  Left gripper: {final_pos[7:19]}")
        print(f"  Right arm: {final_pos[19:26]}")
        print(f"  Right gripper: {final_pos[26:38]}")

        print(f"\n✓ Demo completed successfully!")

        return interpolated_solution

    else:
        print(f"\n✗ Motion planning FAILED")
        print(f"  Status: {result.status}")
        print(f"  Error message: {result.error_message if hasattr(result, 'error_message') else 'Unknown'}")

        print("\nPossible reasons:")
        print("  - Goal pose is unreachable")
        print("  - Collision constraints too tight")
        print("  - Start configuration in collision")

        return None


def demo_with_obstacles():
    """Demonstrate motion planning with additional obstacles."""

    tensor_args = TensorDeviceType(device=torch.device("cuda:0"))
    interpolation_dt = 0.02

    print("\n" + "=" * 80)
    print("Demo 2: Bimanual Planning with Additional Obstacles")
    print("=" * 80)

    # Create motion generator
    motion_gen_cfg = MotionGenConfig.load_from_robot_config(
        robot_cfg="robot/robot_description/configs/robot/bimanual_panda_tesollo.yml",
        world_cfg="robot/robot_description/configs/world/bimanual_table.yml",
        tensor_args=tensor_args,
        interpolation_dt=interpolation_dt,
    )
    motion_gen = MotionGen(motion_gen_cfg)
    motion_gen.warmup()

    # Add custom obstacles
    print("\n[1/3] Adding custom obstacles to the scene...")
    cuboids = [
        # Central obstacle between the arms
        Cuboid(name="obstacle_1", pose=[0.0, 0.0, 1.0, 1, 0, 0, 0], dims=[0.1, 0.1, 0.3]),
        # Left side obstacle
        Cuboid(name="obstacle_2", pose=[0.2, 0.4, 1.0, 1, 0, 0, 0], dims=[0.1, 0.1, 0.2]),
    ]
    world = WorldConfig(cuboid=cuboids)
    motion_gen.update_world(world)
    print("✓ Obstacles added")

    # Define start configuration
    q_start = motion_gen.get_retract_config()

    # Define goal poses (navigating around obstacles)
    print("\n[2/3] Planning trajectory around obstacles...")

    left_ee_goal = Pose(
        position=tensor_args.to_device([[0.4, 0.2, 1.1]]),
        quaternion=tensor_args.to_device([[1, 0, 0, 0]]),
    )

    link_poses = {
        "right_F1_TIP_TOP": Pose(
            position=tensor_args.to_device([[0.4, -0.2, 1.1]]),
            quaternion=tensor_args.to_device([[1, 0, 0, 0]]),
        )
    }

    result = motion_gen.plan_single(q_start, left_ee_goal, MotionGenPlanConfig(), link_poses=link_poses)

    if result.success.item():
        print("✓ Successfully planned trajectory avoiding obstacles!")
        print(f"  Trajectory duration: {len(result.get_interpolated_plan().position) * result.interpolation_dt:.2f}s")
    else:
        print(f"✗ Planning failed: {result.status}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CuRobo Bimanual Motion Generation Examples")
    print("=" * 80)

    # Run basic demo
    trajectory = demo_bimanual_motion_gen()

    # Uncomment to run obstacle avoidance demo
    # demo_with_obstacles()

    print("\n" + "=" * 80)
    print("All demos complete!")
    print("=" * 80)
