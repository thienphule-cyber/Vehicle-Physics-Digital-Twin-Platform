"""
Drive cycle handling.

A drive cycle is a time-series of target vehicle speed, used to drive
the simulation (e.g. WLTP, UDDS, or a custom CSV upload).

This module only deals with loading and preparing drive cycle data
(computing acceleration from speed via finite differences). It does
not perform any powertrain or energy calculations.
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class DriveCycle:
    """
    Time-series representation of a driving cycle.

    Attributes:
        time_s: Array of time stamps [s]
        speed_mps: Array of target vehicle speed [m/s]
        acceleration_mps2: Array of acceleration [m/s^2], derived from speed
        name: Optional label for the drive cycle (e.g. "WLTP", "Custom")
    """

    time_s: np.ndarray
    speed_mps: np.ndarray
    acceleration_mps2: np.ndarray = field(init=False)
    name: str = "unnamed"

    def __post_init__(self) -> None:
        if len(self.time_s) != len(self.speed_mps):
            raise ValueError("time_s and speed_mps must have the same length.")
        if len(self.time_s) < 2:
            raise ValueError("Drive cycle must contain at least 2 samples.")

        self.acceleration_mps2 = self._compute_acceleration()

    def _compute_acceleration(self) -> np.ndarray:
        """
        Compute acceleration from speed using finite differences.

        a[i] = (v[i+1] - v[i]) / (t[i+1] - t[i])

        The last sample repeats the previous acceleration value so the
        array length matches time_s / speed_mps.
        """
        dt = np.diff(self.time_s)
        dv = np.diff(self.speed_mps)

        if np.any(dt <= 0):
            raise ValueError("time_s must be strictly increasing.")

        accel = dv / dt
        # repeat last value so array length matches time_s
        accel = np.append(accel, accel[-1])
        return accel

    @property
    def duration_s(self) -> float:
        """Total duration of the drive cycle [s]."""
        return float(self.time_s[-1] - self.time_s[0])

    @property
    def max_speed_mps(self) -> float:
        """Maximum speed in the drive cycle [m/s]."""
        return float(np.max(self.speed_mps))

    @classmethod
    def from_speed_kmh(
        cls, time_s: np.ndarray, speed_kmh: np.ndarray, name: str = "unnamed"
    ) -> "DriveCycle":
        """
        Convenience constructor when speed is given in km/h instead of m/s.
        """
        speed_mps = np.asarray(speed_kmh, dtype=float) / 3.6
        return cls(time_s=np.asarray(time_s, dtype=float), speed_mps=speed_mps, name=name)