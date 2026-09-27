"""
Generic drivetrain (transmission) equations.

Shared by ICE, Hybrid and BEV powertrains: converts between wheel-side
and engine/motor-side angular velocity and torque through a gear
ratio and final drive ratio.

    omega_wheel = v / r
    omega_engine = omega_wheel * gear_ratio * final_drive_ratio
    T_engine = T_wheel / (gear_ratio * final_drive_ratio * eta_trans)
"""

import math


def wheel_angular_velocity(velocity_mps: float, wheel_radius: float) -> float:
    """
    Compute wheel angular velocity from linear velocity.

    omega_wheel = v / r  [rad/s]
    """
    return velocity_mps / wheel_radius


def engine_angular_velocity(
    wheel_omega: float, gear_ratio: float, final_drive_ratio: float
) -> float:
    """
    Compute engine/motor angular velocity from wheel angular velocity.

    omega_engine = omega_wheel * gear_ratio * final_drive_ratio  [rad/s]
    """
    return wheel_omega * gear_ratio * final_drive_ratio


def engine_torque_from_wheel_torque(
    wheel_torque: float,
    gear_ratio: float,
    final_drive_ratio: float,
    transmission_efficiency: float,
) -> float:
    """
    Compute required engine/motor torque to produce a given wheel
    torque, accounting for transmission losses.

    T_engine = T_wheel / (gear_ratio * final_drive_ratio * eta_trans)
    """
    total_ratio = gear_ratio * final_drive_ratio
    if total_ratio == 0:
        raise ValueError("Combined gear ratio cannot be zero.")
    return wheel_torque / (total_ratio * transmission_efficiency)


def rad_per_s_to_rpm(omega_rad_s: float) -> float:
    """Convert angular velocity from rad/s to RPM."""
    return omega_rad_s * 60.0 / (2.0 * math.pi)


def rpm_to_rad_per_s(rpm: float) -> float:
    """Convert angular velocity from RPM to rad/s."""
    return rpm * 2.0 * math.pi / 60.0