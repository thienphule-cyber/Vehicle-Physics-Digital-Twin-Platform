"""
Longitudinal vehicle dynamics.

Implements the core physical equations shared by ICE, Hybrid and BEV
vehicles:

    F_traction = F_rolling + F_aero + F_grade + F_acc

This module is intentionally independent of any powertrain or web
framework code. It only knows about forces, torques and power at the
wheel level.
"""

import math
from dataclasses import dataclass

from app.models.vehicle import Vehicle

# Standard gravitational acceleration [m/s^2]
GRAVITY = 9.81


@dataclass
class Environment:
    """
    Environmental / road conditions affecting vehicle dynamics.

    Attributes:
        air_density: Air density [kg/m^3], ~1.225 at sea level, 15°C
        road_grade_rad: Road grade angle [rad], positive = uphill
        wind_speed: Headwind speed [m/s], positive = opposing motion
    """

    air_density: float = 1.225
    road_grade_rad: float = 0.0
    wind_speed: float = 0.0


def rolling_resistance_force(vehicle: Vehicle) -> float:
    """
    Compute rolling resistance force.

    F_rolling = Crr * m * g
    """
    return vehicle.rolling_resistance_coefficient * vehicle.mass * GRAVITY


def aerodynamic_drag_force(
    vehicle: Vehicle, environment: Environment, velocity: float
) -> float:
    """
    Compute aerodynamic drag force.

    F_aero = 0.5 * rho * Cd * A * v_rel^2

    The relative velocity accounts for headwind. Sign is preserved so
    that drag always opposes the vehicle's direction of travel.
    """
    relative_velocity = velocity + environment.wind_speed
    force_magnitude = (
        0.5
        * environment.air_density
        * vehicle.drag_coefficient
        * vehicle.frontal_area
        * relative_velocity**2
    )
    return math.copysign(force_magnitude, relative_velocity)


def grade_force(vehicle: Vehicle, environment: Environment) -> float:
    """
    Compute force due to road grade (gravity component along the slope).

    F_grade = m * g * sin(theta)
    """
    return vehicle.mass * GRAVITY * math.sin(environment.road_grade_rad)


def acceleration_force(vehicle: Vehicle, acceleration: float) -> float:
    """
    Compute inertial force required for a given acceleration.

    F_acc = m * a
    """
    return vehicle.mass * acceleration


def traction_force(
    vehicle: Vehicle,
    environment: Environment,
    velocity: float,
    acceleration: float,
) -> float:
    """
    Compute total traction force required at the wheel.

    F_traction = F_rolling + F_aero + F_grade + F_acc

    Note: rolling resistance is only applied when the vehicle is moving,
    otherwise a stationary vehicle would show a nonzero resistance force.
    """
    f_rolling = rolling_resistance_force(vehicle) if velocity != 0 else 0.0
    f_aero = aerodynamic_drag_force(vehicle, environment, velocity)
    f_grade = grade_force(vehicle, environment)
    f_acc = acceleration_force(vehicle, acceleration)

    return f_rolling + f_aero + f_grade + f_acc


def wheel_torque(traction_force_value: float, vehicle: Vehicle) -> float:
    """
    Compute wheel torque from traction force.

    T_wheel = F_traction * r
    """
    return traction_force_value * vehicle.wheel_radius


def wheel_power(traction_force_value: float, velocity: float) -> float:
    """
    Compute wheel power from traction force and velocity.

    P_wheel = F_traction * v
    """
    return traction_force_value * velocity