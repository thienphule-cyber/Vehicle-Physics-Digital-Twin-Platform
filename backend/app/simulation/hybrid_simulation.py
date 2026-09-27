"""
Hybrid vehicle simulation.

Combines longitudinal vehicle dynamics with the hybrid powertrain
(ICE + motor + battery, rule-based control) model.
"""

from dataclasses import dataclass

import numpy as np

from app.models.vehicle import Vehicle
from app.models.hybrid import HybridPowertrain
from app.physics.longitudinal import Environment, traction_force, wheel_torque
from app.physics.drivetrain import wheel_angular_velocity
from app.physics.energy import fuel_energy_to_volume
from app.simulation.drive_cycle import DriveCycle


@dataclass
class HybridSimulationResult:
    """Time-series output of a hybrid vehicle simulation."""

    time_s: np.ndarray
    velocity_mps: np.ndarray

    ice_torque_nm: np.ndarray
    ice_rpm: np.ndarray
    ice_power_w: np.ndarray
    fuel_power_w: np.ndarray

    motor_torque_nm: np.ndarray
    motor_rpm: np.ndarray
    motor_power_w: np.ndarray

    battery_power_w: np.ndarray
    soc: np.ndarray

    fuel_lhv_j_per_l: float

    def summary(self) -> dict:
        distance_m = float(np.trapezoid(self.velocity_mps, self.time_s))

        total_fuel_energy_j = float(np.trapezoid(self.fuel_power_w, self.time_s))
        total_fuel_volume_l = fuel_energy_to_volume(
            total_fuel_energy_j, self.fuel_lhv_j_per_l
        )

        regen_energy_j = float(
            -np.trapezoid(np.clip(self.battery_power_w, None, 0), self.time_s)
        )

        return {
            "distance_km": distance_m / 1000.0,
            "max_speed_kmh": float(np.max(self.velocity_mps)) * 3.6,
            "peak_ice_torque_nm": float(np.max(np.abs(self.ice_torque_nm))),
            "peak_motor_torque_nm": float(np.max(np.abs(self.motor_torque_nm))),
            "final_soc_pct": float(self.soc[-1]) * 100.0,
            "total_fuel_volume_l": total_fuel_volume_l,
            "regen_energy_kwh": regen_energy_j / 3.6e6,
            "avg_fuel_consumption_l_per_100km": (
                total_fuel_volume_l / (distance_m / 1000.0) * 100.0
                if distance_m > 0
                else 0.0
            ),
        }


class HybridVehicleSimulation:
    """Runs a drive cycle through vehicle dynamics + hybrid powertrain."""

    def __init__(
        self,
        vehicle: Vehicle,
        environment: Environment,
        drive_cycle: DriveCycle,
        powertrain: HybridPowertrain,
    ) -> None:
        self.vehicle = vehicle
        self.environment = environment
        self.drive_cycle = drive_cycle
        self.powertrain = powertrain

    def run(self) -> HybridSimulationResult:
        n = len(self.drive_cycle.time_s)

        ice_t = np.zeros(n)
        ice_rpm = np.zeros(n)
        ice_p = np.zeros(n)
        fuel_p = np.zeros(n)

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

            ice_t[i] = step_result["ice_torque_nm"]
            ice_rpm[i] = step_result["ice_rpm"]
            ice_p[i] = step_result["ice_power_w"]
            fuel_p[i] = step_result["fuel_power_w"]

            motor_t[i] = step_result["motor_torque_nm"]
            motor_rpm[i] = step_result["motor_rpm"]
            motor_p[i] = step_result["motor_power_w"]

            battery_p[i] = step_result["battery_power_w"]
            soc[i] = step_result["soc"]

        return HybridSimulationResult(
            time_s=self.drive_cycle.time_s,
            velocity_mps=self.drive_cycle.speed_mps,
            ice_torque_nm=ice_t,
            ice_rpm=ice_rpm,
            ice_power_w=ice_p,
            fuel_power_w=fuel_p,
            motor_torque_nm=motor_t,
            motor_rpm=motor_rpm,
            motor_power_w=motor_p,
            battery_power_w=battery_p,
            soc=soc,
            fuel_lhv_j_per_l=self.powertrain.ice.fuel_lhv_j_per_l,
        )