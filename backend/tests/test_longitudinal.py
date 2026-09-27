"""
Basic sanity tests for Phase 1 physics core.

These tests validate that the longitudinal dynamics equations behave
as expected under simple, hand-checkable conditions.
"""

import math

import numpy as np
import pytest

from app.models.vehicle import Vehicle
from app.physics.longitudinal import (
    Environment,
    GRAVITY,
    rolling_resistance_force,
    aerodynamic_drag_force,
    grade_force,
    acceleration_force,
    traction_force,
    wheel_torque,
    wheel_power,
)
from app.simulation.drive_cycle import DriveCycle


@pytest.fixture
def sample_vehicle() -> Vehicle:
    return Vehicle(
        mass=1600.0,
        wheel_radius=0.34,
        drag_coefficient=0.29,
        frontal_area=2.2,
        rolling_resistance_coefficient=0.012,
    )


@pytest.fixture
def flat_environment() -> Environment:
    return Environment(air_density=1.225, road_grade_rad=0.0, wind_speed=0.0)


def test_rolling_resistance_force(sample_vehicle):
    expected = 0.012 * 1600.0 * GRAVITY
    assert math.isclose(rolling_resistance_force(sample_vehicle), expected, rel_tol=1e-6)


def test_aerodynamic_drag_force_zero_velocity(sample_vehicle, flat_environment):
    assert aerodynamic_drag_force(sample_vehicle, flat_environment, 0.0) == 0.0


def test_aerodynamic_drag_force_positive_velocity(sample_vehicle, flat_environment):
    force = aerodynamic_drag_force(sample_vehicle, flat_environment, 20.0)
    assert force > 0


def test_grade_force_flat_road(sample_vehicle, flat_environment):
    assert grade_force(sample_vehicle, flat_environment) == 0.0


def test_grade_force_uphill(sample_vehicle):
    uphill = Environment(road_grade_rad=math.radians(5))
    force = grade_force(sample_vehicle, uphill)
    assert force > 0


def test_acceleration_force(sample_vehicle):
    force = acceleration_force(sample_vehicle, 1.0)
    assert force == sample_vehicle.mass


def test_traction_force_constant_speed_flat_road(sample_vehicle, flat_environment):
    """
    At constant speed on a flat road, traction force should equal
    rolling resistance + aerodynamic drag only (no grade, no accel term).
    """
    velocity = 20.0
    force = traction_force(sample_vehicle, flat_environment, velocity, acceleration=0.0)

    expected = rolling_resistance_force(sample_vehicle) + aerodynamic_drag_force(
        sample_vehicle, flat_environment, velocity
    )
    assert math.isclose(force, expected, rel_tol=1e-6)


def test_wheel_torque_and_power(sample_vehicle):
    force = 1000.0
    velocity = 20.0

    torque = wheel_torque(force, sample_vehicle)
    power = wheel_power(force, velocity)

    assert math.isclose(torque, force * sample_vehicle.wheel_radius, rel_tol=1e-6)
    assert math.isclose(power, force * velocity, rel_tol=1e-6)


def test_drive_cycle_acceleration_computation():
    time_s = np.array([0.0, 1.0, 2.0, 3.0])
    speed_mps = np.array([0.0, 2.0, 4.0, 4.0])

    cycle = DriveCycle(time_s=time_s, speed_mps=speed_mps, name="test_cycle")

    expected_accel = np.array([2.0, 2.0, 0.0, 0.0])
    assert np.allclose(cycle.acceleration_mps2, expected_accel)


def test_drive_cycle_duration_and_max_speed():
    time_s = np.array([0.0, 1.0, 2.0])
    speed_mps = np.array([0.0, 10.0, 20.0])

    cycle = DriveCycle(time_s=time_s, speed_mps=speed_mps)

    assert cycle.duration_s == 2.0
    assert cycle.max_speed_mps == 20.0