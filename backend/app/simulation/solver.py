"""
Vehicle dynamics simulation engine.

Phase 2 scope: run a drive cycle through the longitudinal dynamics
model (no powertrain yet — that is introduced in Phase 3/4). The
vehicle is assumed to follow the drive cycle's target speed exactly,
so this engine computes the resulting forces, torque and power at
the wheel for every timestep.

This produces the first full time-series simulation output, which
later phases will extend with powertrain-specific quantities
(engine torque, motor power, battery SOC, etc).
"""

from dataclasses import dataclass, field

import numpy as np

from app.models.vehicle import Vehicle
from app.physics.longitudinal import (
    Environment,
    traction_force,
    rolling_resistance_force,
    aerodynamic_drag_force,
    grade_force,
    acceleration_force,
    wheel_torque,
    wheel_power,
)
from app.simulation.drive_cycle import DriveCycle


@dataclass
class SimulationResult:
    """
    Time-series output of a vehicle dynamics simulation.

    All arrays share the same length and index alignment with
    drive_cycle.time_s.
    """

    time_s: np.ndarray
    velocity_mps: np.ndarray
    acceleration_mps2: np.ndarray

    f_rolling_n: np.ndarray
    f_aero_n: np.ndarray
    f_grade_n: np.ndarray
    f_acc_n: np.ndarray
    f_traction_n: np.ndarray

    wheel_torque_nm: np.ndarray
    wheel_power_w: np.ndarray

    def summary(self) -> dict:
        """Compute a few scalar summary metrics for quick inspection."""
        distance_m = float(np.trapezoid(self.velocity_mps, self.time_s))
        return {
            "duration_s": float(self.time_s[-1] - self.time_s[0]),
            "distance_km": distance_m / 1000.0,
            "max_speed_kmh": float(np.max(self.velocity_mps)) * 3.6,
            "max_traction_force_n": float(np.max(self.f_traction_n)),
            "max_wheel_power_kw": float(np.max(self.wheel_power_w)) / 1000.0,
            "peak_wheel_torque_nm": float(np.max(self.wheel_torque_nm)),
        }


class VehicleDynamicsSimulation:
    """
    Runs a drive cycle through the longitudinal dynamics model,
    computing vehicle-level forces, torque and power at every
    timestep.
    """

    def __init__(
        self,
        vehicle: Vehicle,
        environment: Environment,
        drive_cycle: DriveCycle,
    ) -> None:
        self.vehicle = vehicle
        self.environment = environment
        self.drive_cycle = drive_cycle

    def run(self) -> SimulationResult:
        """
        Execute the simulation over the full drive cycle.

        For each timestep:
            velocity     <- drive_cycle.speed_mps[i]
            acceleration <- drive_cycle.acceleration_mps2[i]
            forces       <- longitudinal dynamics equations
            torque/power <- derived from traction force
        """
        n = len(self.drive_cycle.time_s)

        f_rolling = np.zeros(n)
        f_aero = np.zeros(n)
        f_grade = np.zeros(n)
        f_acc = np.zeros(n)
        f_traction = np.zeros(n)
        torque = np.zeros(n)
        power = np.zeros(n)

        for i in range(n):
            v = float(self.drive_cycle.speed_mps[i])
            a = float(self.drive_cycle.acceleration_mps2[i])

            f_rolling[i] = rolling_resistance_force(self.vehicle) if v != 0 else 0.0
            f_aero[i] = aerodynamic_drag_force(self.vehicle, self.environment, v)
            f_grade[i] = grade_force(self.vehicle, self.environment)
            f_acc[i] = acceleration_force(self.vehicle, a)

            f_traction[i] = traction_force(self.vehicle, self.environment, v, a)
            torque[i] = wheel_torque(f_traction[i], self.vehicle)
            power[i] = wheel_power(f_traction[i], v)

        return SimulationResult(
            time_s=self.drive_cycle.time_s,
            velocity_mps=self.drive_cycle.speed_mps,
            acceleration_mps2=self.drive_cycle.acceleration_mps2,
            f_rolling_n=f_rolling,
            f_aero_n=f_aero,
            f_grade_n=f_grade,
            f_acc_n=f_acc,
            f_traction_n=f_traction,
            wheel_torque_nm=torque,
            wheel_power_w=power,
        )