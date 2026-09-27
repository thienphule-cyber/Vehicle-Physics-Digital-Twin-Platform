"""
Tests for Phase 2 - vehicle dynamics simulation engine.
"""

import math

import pytest

from app.models.vehicle import Vehicle
from app.physics.longitudinal import Environment
from app.simulation.solver import VehicleDynamicsSimulation
from app.simulation.standard_cycles import simple_test_cycle


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


def test_simulation_runs_and_returns_matching_length_arrays(
    sample_vehicle, flat_environment
):
    drive_cycle = simple_test_cycle()
    simulation = VehicleDynamicsSimulation(
        vehicle=sample_vehicle, environment=flat_environment, drive_cycle=drive_cycle
    )

    result = simulation.run()

    n = len(drive_cycle.time_s)
    assert len(result.velocity_mps) == n
    assert len(result.f_traction_n) == n
    assert len(result.wheel_torque_nm) == n
    assert len(result.wheel_power_w) == n


def test_simulation_zero_velocity_has_zero_rolling_resistance(
    sample_vehicle, flat_environment
):
    drive_cycle = simple_test_cycle()
    simulation = VehicleDynamicsSimulation(
        vehicle=sample_vehicle, environment=flat_environment, drive_cycle=drive_cycle
    )
    result = simulation.run()

    # first sample of simple_test_cycle starts at 0 speed
    assert result.velocity_mps[0] == 0.0
    assert result.f_rolling_n[0] == 0.0


def test_simulation_summary_contains_expected_keys(sample_vehicle, flat_environment):
    drive_cycle = simple_test_cycle()
    simulation = VehicleDynamicsSimulation(
        vehicle=sample_vehicle, environment=flat_environment, drive_cycle=drive_cycle
    )
    result = simulation.run()
    summary = result.summary()

    expected_keys = {
        "duration_s",
        "distance_km",
        "max_speed_kmh",
        "max_traction_force_n",
        "max_wheel_power_kw",
        "peak_wheel_torque_nm",
    }
    assert expected_keys.issubset(summary.keys())


def test_simulation_max_speed_matches_cycle(sample_vehicle, flat_environment):
    drive_cycle = simple_test_cycle()
    simulation = VehicleDynamicsSimulation(
        vehicle=sample_vehicle, environment=flat_environment, drive_cycle=drive_cycle
    )
    result = simulation.run()
    summary = result.summary()

    expected_max_kmh = drive_cycle.max_speed_mps * 3.6
    assert math.isclose(summary["max_speed_kmh"], expected_max_kmh, rel_tol=1e-6)