"""
Built-in standard drive cycles.

Phase 2 needs at least one ready-to-use drive cycle so the simulation
engine can be tested end-to-end without requiring a CSV upload yet
(CSV upload support is added in the API layer / later phase).

This module provides a small synthetic cycle for development and
testing. Real WLTP/UDDS cycle data can be added later as CSV files
under data/drive_cycles/ and loaded the same way.
"""

import numpy as np

from app.simulation.drive_cycle import DriveCycle


def simple_test_cycle() -> DriveCycle:
    """
    A short synthetic cycle: accelerate, cruise, decelerate, stop.
    Useful for quick manual testing and unit tests.
    """
    time_s = np.arange(0, 61, 1, dtype=float)  # 0..60 s
    speed_kmh = np.concatenate(
        [
            np.linspace(0, 60, 20),   # accelerate 0 -> 60 km/h over 20 s
            np.full(20, 60.0),        # cruise at 60 km/h for 20 s
            np.linspace(60, 0, 21),   # decelerate 60 -> 0 km/h over 21 s
        ]
    )
    return DriveCycle.from_speed_kmh(time_s, speed_kmh, name="simple_test_cycle")