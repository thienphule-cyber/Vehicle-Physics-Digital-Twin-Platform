"""
ICE vehicle simulation.

Combines the longitudinal vehicle dynamics (Phase 1/2) with the ICE
powertrain model (Phase 3): for each timestep, the wheel torque
demand computed from vehicle dynamics is fed into the ICE powertrain
to obtain engine torque, RPM, power and fuel consumption.
"""

from dataclasses import dataclass

import numpy as np

from app.models.vehicle import Vehicle
from app.models.ice import ICEPowertrain
from app.physics.longitudinal import (
    Environment,
    traction_force,
    wheel_torque,
)
from app.physics.drivetrain import wheel_angular_velocity
from app.physics.energy import fuel_energy_to_volume
from app.simulation.drive_cycle import DriveCycle


@dataclass
class ICESimulationResult:
    """Time-series output of an ICE vehicle simulation."""

    time_s: np.ndarray
    velocity_mps: np.ndarray

    wheel_torque_nm: np.ndarray
    wheel_power_w: np.ndarray

    engine_torque_nm: np.ndarray
    engine_rpm: np.ndarray
    engine_power_w: np.ndarray
    fuel_power_w: np.ndarray

    total_fuel_energy_j: float
    total_fuel_volume_l: float

    def summary(self) -> dict:
        distance_m = float(np.trapezoid(self.velocity_mps, self.time_s))
        return {
            "distance_km": distance_m / 1000.0,
            "max_speed_kmh": float(np.max(self.velocity_mps)) * 3.6,
            "peak_engine_torque_nm": float(np.max(np.abs(self.engine_torque_nm))),
            "peak_engine_power_kw": float(np.max(self.engine_power_w)) / 1000.0,
            "max_engine_rpm": float(np.max(self.engine_rpm)),
            "total_fuel_volume_l": self.total_fuel_volume_l,
            "avg_fuel_consumption_l_per_100km": (
                self.total_fuel_volume_l / (distance_m / 1000.0) * 100.0
                if distance_m > 0
                else 0.0
            ),
        }


class ICEVehicleSimulation:
    """
    Runs a drive cycle through the longitudinal dynamics model and
    the ICE powertrain model together.
    """

    def __init__(
        self,
        vehicle: Vehicle,
        environment: Environment,
        drive_cycle: DriveCycle,
        powertrain: ICEPowertrain,
    ) -> None:
        self.vehicle = vehicle
        self.environment = environment
        self.drive_cycle = drive_cycle
        self.powertrain = powertrain

    def run(self) -> ICESimulationResult:
        n = len(self.drive_cycle.time_s)

        wheel_t = np.zeros(n)
        wheel_p = np.zeros(n)
        engine_t = np.zeros(n)
        engine_rpm = np.zeros(n)
        engine_p = np.zeros(n)
        fuel_p = np.zeros(n)

        for i in range(n):
            v = float(self.drive_cycle.speed_mps[i])
            a = float(self.drive_cycle.acceleration_mps2[i])

            f_traction = traction_force(self.vehicle, self.environment, v, a)
            t_wheel = wheel_torque(f_traction, self.vehicle)
            omega_wheel = wheel_angular_velocity(v, self.vehicle.wheel_radius)

            engine_state = self.powertrain.calculate(t_wheel, omega_wheel)

            wheel_t[i] = t_wheel
            wheel_p[i] = f_traction * v
            engine_t[i] = engine_state["engine_torque_nm"]
            engine_rpm[i] = engine_state["engine_rpm"]
            engine_p[i] = engine_state["engine_power_w"]
            fuel_p[i] = engine_state["fuel_power_w"]

        total_fuel_energy_j = float(np.trapezoid(fuel_p, self.drive_cycle.time_s))
        total_fuel_volume_l = fuel_energy_to_volume(
            total_fuel_energy_j, self.powertrain.fuel_lhv_j_per_l
        )

        return ICESimulationResult(
            time_s=self.drive_cycle.time_s,
            velocity_mps=self.drive_cycle.speed_mps,
            wheel_torque_nm=wheel_t,
            wheel_power_w=wheel_p,
            engine_torque_nm=engine_t,
            engine_rpm=engine_rpm,
            engine_power_w=engine_p,
            fuel_power_w=fuel_p,
            total_fuel_energy_j=total_fuel_energy_j,
            total_fuel_volume_l=total_fuel_volume_l,
        )