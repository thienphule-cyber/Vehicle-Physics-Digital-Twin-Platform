"""
Electric motor model.

Represents a traction motor (used by both BEV and Hybrid powertrains).
Given a wheel torque demand and wheel angular velocity, computes
motor torque, RPM, mechanical power and the corresponding battery
power (accounting for motor + inverter losses), including
regenerative braking when torque demand is negative.
"""

import math
from dataclasses import dataclass

from app.physics.drivetrain import (
    engine_angular_velocity,
    engine_torque_from_wheel_torque,
    rad_per_s_to_rpm,
)


@dataclass
class Motor:
    """
    Parameters describing an electric traction motor + inverter.

    Attributes:
        max_torque_nm: Maximum motor torque (both drive and regen) [N*m]
        max_power_w: Maximum motor power (both drive and regen) [W]
        gear_ratio: Fixed reduction gear ratio
        final_drive_ratio: Final drive ratio (often combined with gear_ratio in BEVs,
            kept separate here for consistency with the ICE model)
        transmission_efficiency: Mechanical efficiency of the gear reduction [0-1]
        motor_efficiency: Motor electrical-to-mechanical efficiency [0-1] (V1 constant)
        inverter_efficiency: Inverter efficiency [0-1] (V1 constant)
        regen_efficiency: Additional efficiency factor applied during
            regenerative braking (captures the fact that not all
            braking torque can be recovered) [0-1]
    """

    max_torque_nm: float
    max_power_w: float
    gear_ratio: float
    final_drive_ratio: float
    transmission_efficiency: float = 0.95
    motor_efficiency: float = 0.92
    inverter_efficiency: float = 0.97
    regen_efficiency: float = 0.7

    def __post_init__(self) -> None:
        if self.max_torque_nm <= 0:
            raise ValueError("max_torque_nm must be positive.")
        if self.max_power_w <= 0:
            raise ValueError("max_power_w must be positive.")
        for name, value in [
            ("transmission_efficiency", self.transmission_efficiency),
            ("motor_efficiency", self.motor_efficiency),
            ("inverter_efficiency", self.inverter_efficiency),
            ("regen_efficiency", self.regen_efficiency),
        ]:
            if not (0 < value <= 1):
                raise ValueError(f"{name} must be in (0, 1].")

    def calculate(self, wheel_torque_nm: float, wheel_omega_rad_s: float) -> dict:
        """
        Compute motor state for one timestep, given the wheel torque
        demand and wheel angular velocity.

        Positive wheel_torque_nm = driving (motor provides torque,
        battery discharges).
        Negative wheel_torque_nm = braking (motor absorbs torque,
        battery charges via regeneration).

        Returns a dict with:
            motor_torque_nm
            motor_omega_rad_s
            motor_rpm
            motor_power_w: mechanical power at the motor shaft
            battery_power_w: electrical power drawn from (+) or
                delivered to (-) the battery
            torque_limited: bool
            power_limited: bool
        """
        motor_omega = engine_angular_velocity(
            wheel_omega_rad_s, self.gear_ratio, self.final_drive_ratio
        )

        requested_torque = engine_torque_from_wheel_torque(
            wheel_torque_nm,
            self.gear_ratio,
            self.final_drive_ratio,
            self.transmission_efficiency,
        )

        torque_limited = abs(requested_torque) > self.max_torque_nm
        motor_torque = max(
            -self.max_torque_nm, min(requested_torque, self.max_torque_nm)
        )

        motor_power = motor_torque * motor_omega

        power_limited = abs(motor_power) > self.max_power_w
        if power_limited and motor_omega != 0:
            capped_power = math.copysign(self.max_power_w, motor_power)
            motor_torque = capped_power / motor_omega
            motor_power = capped_power

        battery_power = self._battery_power_from_motor_power(motor_power)

        return {
            "motor_torque_nm": motor_torque,
            "motor_omega_rad_s": motor_omega,
            "motor_rpm": rad_per_s_to_rpm(motor_omega),
            "motor_power_w": motor_power,
            "battery_power_w": battery_power,
            "torque_limited": torque_limited,
            "power_limited": power_limited,
        }

    def _battery_power_from_motor_power(self, motor_power_w: float) -> float:
        """
        Convert mechanical motor power into electrical battery power.

        Driving (motor_power_w > 0):
            P_battery = P_motor / (eta_motor * eta_inverter)

        Regenerative braking (motor_power_w < 0):
            P_battery = P_motor * eta_motor * eta_inverter * eta_regen
            (negative, i.e. power flows back into the battery)
        """
        if motor_power_w >= 0:
            return motor_power_w / (self.motor_efficiency * self.inverter_efficiency)
        else:
            return (
                motor_power_w
                * self.motor_efficiency
                * self.inverter_efficiency
                * self.regen_efficiency
            )