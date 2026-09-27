"""
ICE (internal combustion engine) powertrain model.

Represents the engine + transmission of a conventional vehicle.
Given a wheel torque demand and wheel angular velocity (from the
longitudinal vehicle dynamics), computes engine torque, RPM, power
and fuel consumption for one timestep.

Phase 3 scope: single fixed gear ratio (no gear shifting logic yet),
constant engine efficiency (no torque/RPM efficiency map yet).
"""

from dataclasses import dataclass

from app.physics.drivetrain import (
    engine_angular_velocity,
    engine_torque_from_wheel_torque,
    rad_per_s_to_rpm,
)
from app.physics.energy import fuel_power_from_engine_power


@dataclass
class ICEPowertrain:
    """
    Parameters describing an ICE powertrain.

    Attributes:
        max_torque_nm: Maximum engine torque [N*m]
        max_power_w: Maximum engine power [W]
        gear_ratio: Fixed gear ratio (V1 simplification, no shifting)
        final_drive_ratio: Final drive (differential) ratio
        transmission_efficiency: Mechanical efficiency of the transmission [0-1]
        engine_efficiency: Constant engine thermal efficiency [0-1] (V1 simplification)
        fuel_lhv_j_per_l: Fuel lower heating value [J/L]
        max_rpm: Maximum allowed engine speed [RPM], used for saturation/warnings
    """

    max_torque_nm: float
    max_power_w: float
    gear_ratio: float
    final_drive_ratio: float
    transmission_efficiency: float
    engine_efficiency: float
    fuel_lhv_j_per_l: float
    max_rpm: float = 7000.0

    def __post_init__(self) -> None:
        if self.max_torque_nm <= 0:
            raise ValueError("max_torque_nm must be positive.")
        if self.max_power_w <= 0:
            raise ValueError("max_power_w must be positive.")
        if not (0 < self.transmission_efficiency <= 1):
            raise ValueError("transmission_efficiency must be in (0, 1].")
        if not (0 < self.engine_efficiency <= 1):
            raise ValueError("engine_efficiency must be in (0, 1].")

    def calculate(self, wheel_torque_nm: float, wheel_omega_rad_s: float) -> dict:
        """
        Compute engine state for one timestep, given the wheel torque
        demand (from vehicle dynamics) and wheel angular velocity.

        Returns a dict with:
            engine_torque_nm
            engine_omega_rad_s
            engine_rpm
            engine_power_w
            fuel_power_w
            torque_limited: bool, True if requested torque exceeded max_torque_nm
            power_limited: bool, True if requested power exceeded max_power_w
        """
        engine_omega = engine_angular_velocity(
            wheel_omega_rad_s, self.gear_ratio, self.final_drive_ratio
        )

        requested_torque = engine_torque_from_wheel_torque(
            wheel_torque_nm,
            self.gear_ratio,
            self.final_drive_ratio,
            self.transmission_efficiency,
        )

        torque_limited = abs(requested_torque) > self.max_torque_nm
        engine_torque = max(
            -self.max_torque_nm, min(requested_torque, self.max_torque_nm)
        )

        engine_power = engine_torque * engine_omega

        power_limited = abs(engine_power) > self.max_power_w
        if power_limited and engine_omega != 0:
            capped_power = math.copysign(self.max_power_w, engine_power)
            engine_torque = capped_power / engine_omega
            engine_power = capped_power

        fuel_power = fuel_power_from_engine_power(engine_power, self.engine_efficiency)

        return {
            "engine_torque_nm": engine_torque,
            "engine_omega_rad_s": engine_omega,
            "engine_rpm": rad_per_s_to_rpm(engine_omega),
            "engine_power_w": engine_power,
            "fuel_power_w": fuel_power,
            "torque_limited": torque_limited,
            "power_limited": power_limited,
        }


import math  # noqa: E402  (placed here to keep dataclass definition readable above)