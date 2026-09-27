"""
BEV vehicle simulation.

Combines longitudinal vehicle dynamics with the BEV powertrain
(motor + battery) model, stepping SOC forward over the drive cycle.
"""

from dataclasses import dataclass

import numpy as np

from app.models.vehicle import Vehicle
from app.models.bev import BEVPowertrain
from app.physics.longitudinal import Environment, traction_force, wheel_torque
from app.physics.drivetrain import wheel_angular_velocity
from app.simulation.drive_cycle import DriveCycle


@dataclass
class BEVSimulationResult:
    """Time-series output of a BEV vehicle simulation."""

    time_s: np.ndarray
    velocity_mps: np.ndarray

    motor_torque_nm: np.ndarray
    motor_rpm: np.ndarray
    motor_power_w: np.ndarray
    battery_power_w: np.ndarray
    soc: np.ndarray

    def summary(self) -> dict:
        distance_m = float(np.trapezoid(self.velocity_mps, self.time_s))
        total_energy_j = float(
            np.trapezoid(np.clip(self.battery_power_w, 0, None), self.time_s)
        )
        regen_energy_j = float(
            -np.trapezoid(np.clip(self.battery_power_w, None, 0), self.time_s)
        )
        return {
            "distance_km": distance_m / 1000.0,
            "max_speed_kmh": float(np.max(self.velocity_mps)) * 3.6,
            "peak_motor_torque_nm": float(np.max(np.abs(self.motor_torque_nm))),
            "peak_motor_power_kw": float(np.max(self.motor_power_w)) / 1000.0,
            "final_soc_pct": float(self.soc[-1]) * 100.0,
            "total_energy_kwh": total_energy_j / 3.6e6,
            "regen_energy_kwh": regen_energy_j / 3.6e6,
            "avg_consumption_kwh_per_100km": (
                (total_energy_j / 3.6e6) / (distance_m / 1000.0) * 100.0
                if distance_m > 0
                else 0.0
            ),
        }


class BEVVehicleSimulation:
    """Runs a drive cycle through vehicle dynamics + BEV powertrain."""

    def __init__(
        self,
        vehicle: Vehicle,
        environment: Environment,
        drive_cycle: DriveCycle,
        powertrain: BEVPowertrain,
    ) -> None:
        self.vehicle = vehicle
        self.environment = environment
        self.drive_cycle = drive_cycle
        self.powertrain = powertrain

    def run(self) -> BEVSimulationResult:
        n = len(self.drive_cycle.time_s)

        motor_t = np.zeros(n)
        motor_rpm = np.zeros(n)
        motor_p = np.zeros(n)
        battery_p = np.zeros(n)
        soc = np.zeros(n)

        state = self.powertrain.create_state()

        for i in range(n):
            v = float(self.drive_cycle.speed_mps[i])
            a = float(self.drive_cycle.acceleration_mps2[i])

            dt = (
                float(self.drive_cycle.time_s[i] - self.drive_cycle.time_s[i - 1])
                if i > 0
                else float(self.drive_cycle.time_s[1] - self.drive_cycle.time_s[0])
            )

            f_traction = traction_force(self.vehicle, self.environment, v, a)
            t_wheel = wheel_torque(f_traction, self.vehicle)
            omega_wheel = wheel_angular_velocity(v, self.vehicle.wheel_radius)

            step_result = state.step(t_wheel, omega_wheel, dt)

            motor_t[i] = step_result["motor_torque_nm"]
            motor_rpm[i] = step_result["motor_rpm"]
            motor_p[i] = step_result["motor_power_w"]
            battery_p[i] = step_result["battery_power_w"]
            soc[i] = step_result["soc"]

        return BEVSimulationResult(
            time_s=self.drive_cycle.time_s,
            velocity_mps=self.drive_cycle.speed_mps,
            motor_torque_nm=motor_t,
            motor_rpm=motor_rpm,
            motor_power_w=motor_p,
            battery_power_w=battery_p,
            soc=soc,
        )