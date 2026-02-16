"""
Generate collision spheres for Tesollo DG3F hand based on URDF analysis.

This tool analyzes the URDF link dimensions and generates appropriate
collision sphere configurations.
"""

import math


def analyze_urdf_link_dimensions():
    """
    Based on panda_w_tesollo.urdf analysis:

    Link dimensions (from inertial mass and inertia):
    - delto_base_link: mass=0.370kg, roughly cylindrical base
    - F*_01: mass=0.061kg, first finger segment
    - F*_02: mass=0.025kg, second finger segment
    - F*_03: mass=0.051kg, third finger segment
    - F*_04: mass=0.058kg, fourth finger segment
    - F*_TIP: mass=0.013kg, fingertip

    Joint offsets (xyz in meters):
    - delto_base → F*_01: varies by finger
      F1: [0.0265, 0, 0]
      F2: [-0.01334, 0.023, 0]
      F3: [-0.01334, -0.023, 0]
    - F*_01 → F*_02: [0, 0, 0] (rotation only)
    - F*_02 → F*_03: [0.02022, 0, 0.03136]
    - F*_03 → F*_04: [0.0434, 0, 0]
    - F*_04 → F*_TIP: [0.028, 0, 0] (estimated from mass center)
    - F*_TIP → F*_TIP_TOP: [0.058, 0, 0.002]
    """

    # Estimated sphere radii based on mass and typical finger dimensions
    # These are conservative (slightly larger) for safe collision avoidance
    sphere_config = {
        "delto_base_link": [
            {"center": [0.0, 0.0, 0.0], "radius": 0.035, "comment": "Base center"},
            {"center": [0.0, 0.0, -0.02], "radius": 0.035, "comment": "Base bottom"},
        ],

        # Finger 1
        "F1_01": [
            {"center": [0.0, 0.0, 0.0], "radius": 0.015, "comment": "First segment base"},
        ],
        "F1_02": [
            {"center": [0.01, 0.0, 0.015], "radius": 0.012, "comment": "Second segment mid"},
        ],
        "F1_03": [
            {"center": [0.02, 0.0, 0.0], "radius": 0.012, "comment": "Third segment mid"},
        ],
        "F1_04": [
            {"center": [0.01, 0.0, 0.0], "radius": 0.012, "comment": "Fourth segment mid"},
        ],
        "F1_TIP": [
            {"center": [0.02, 0.0, 0.0], "radius": 0.012, "comment": "Fingertip base"},
            {"center": [0.04, 0.0, 0.0], "radius": 0.01, "comment": "Fingertip end"},
        ],

        # Finger 2 (same dimensions as F1)
        "F2_01": [
            {"center": [0.0, 0.0, 0.0], "radius": 0.015},
        ],
        "F2_02": [
            {"center": [0.01, 0.0, 0.015], "radius": 0.012},
        ],
        "F2_03": [
            {"center": [0.02, 0.0, 0.0], "radius": 0.012},
        ],
        "F2_04": [
            {"center": [0.01, 0.0, 0.0], "radius": 0.012},
        ],
        "F2_TIP": [
            {"center": [0.02, 0.0, 0.0], "radius": 0.012},
            {"center": [0.04, 0.0, 0.0], "radius": 0.01},
        ],

        # Finger 3 (same dimensions as F1)
        "F3_01": [
            {"center": [0.0, 0.0, 0.0], "radius": 0.015},
        ],
        "F3_02": [
            {"center": [0.01, 0.0, 0.015], "radius": 0.012},
        ],
        "F3_03": [
            {"center": [0.02, 0.0, 0.0], "radius": 0.012},
        ],
        "F3_04": [
            {"center": [0.01, 0.0, 0.0], "radius": 0.012},
        ],
        "F3_TIP": [
            {"center": [0.02, 0.0, 0.0], "radius": 0.012},
            {"center": [0.04, 0.0, 0.0], "radius": 0.01},
        ],
    }

    return sphere_config


def generate_yml(sphere_config, prefix=""):
    """Generate YAML configuration for collision spheres."""

    lines = []

    for link_name, spheres in sphere_config.items():
        prefixed_name = f"{prefix}{link_name}" if prefix else link_name
        lines.append(f"  {prefixed_name}:")

        for sphere in spheres:
            center = sphere["center"]
            radius = sphere["radius"]
            lines.append(f"    - center: [{center[0]}, {center[1]}, {center[2]}]")
            lines.append(f"      radius: {radius}")
            if "comment" in sphere:
                lines[-2] = lines[-2] + f"  # {sphere['comment']}"
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 80)
    print("Tesollo DG3F Hand - Collision Sphere Generator")
    print("=" * 80)
    print("\nAnalyzing URDF dimensions...")

    config = analyze_urdf_link_dimensions()

    # Count total spheres
    total = sum(len(spheres) for spheres in config.values())
    print(f"\nGenerated {total} collision spheres for {len(config)} links")

    print("\n" + "=" * 80)
    print("Single-arm configuration:")
    print("=" * 80)
    print("\ncollision_spheres:")
    print(generate_yml(config))

    print("\n" + "=" * 80)
    print("Bimanual configuration (left + right):")
    print("=" * 80)
    print("\ncollision_spheres:")
    print(generate_yml(config, prefix="left_"))
    print(generate_yml(config, prefix="right_"))

    print("\n" + "=" * 80)
    print("Note: These spheres are based on URDF analysis.")
    print("You may need to adjust radii based on actual mesh geometry.")
    print("=" * 80)
