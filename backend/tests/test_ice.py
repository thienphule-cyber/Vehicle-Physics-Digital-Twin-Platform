"""
Tests for Phase 3 - ICE powertrain model and simulation.
"""

import math

import pytest

from app.models.vehicle import Vehicle
from app.models.ice import ICEPowertrain
from app.physics.longitudinal import Environment
from app.physics.energy import GASOLINE_LHV_J_PER_L
from app.physics.drivetrain import wheel_angular_velocity
from app.simulation.ice_simulation import ICEVehicleSimulation
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


@pytest.fixture
def sample_ice_powertrain() -> ICEPowertrain:
    return ICEPowertrain(
        max_torque_nm=250.0,
        max_power_w=110_000.0,
        gear_ratio=3.5,
        final_drive_ratio=3.9,
        transmission_efficiency=0.92,
        engine_efficiency=0.30,
        fuel_lhv_j_per_l=GASOLINE_LHV_J_PER_L,
    )


def test_ice_powertrain_zero_demand_has_zero_fuel_power(sample_ice_powertrain):
    result = sample_ice_powertrain.calculate(wheel_torque_nm=0.0, wheel_omega_rad_s=10.0)
    assert result["engine_torque_nm"] == pytest.approx(0.0, abs=1e-6)
    assert result["fuel_power_w"] == pytest.approx(0.0, abs=1e-6)


def test_ice_powertrain_torque_is_limited(sample_ice_powertrain):
    # Request an unrealistically large wheel torque to force saturation
    result = sample_ice_powertrain.calculate(
        wheel_torque_nm=100_000.0, wheel_omega_rad_s=10.0
    )
    assert result["torque_limited"] is True
    assert abs(result["engine_torque_nm"]) <= sample_ice_powertrain.max_torque_nm + 1e-6


def test_ice_powertrain_positive_power_consumes_fuel(sample_ice_powertrain):
    result = sample_ice_powertrain.calculate(wheel_torque_nm=200.0, wheel_omega_rad_s=50.0)
    assert result["engine_power_w"] > 0
    assert result["fuel_power_w"] > 0
    expected_fuel_power = result["engine_power_w"] / sample_ice_powertrain.engine_efficiency
    assert result["fuel_power_w"] == pytest.approx(expected_fuel_power, rel=1e-6)


def test_ice_simulation_runs_and_returns_matching_length_arrays(
    sample_vehicle, flat_environment, sample_ice_powertrain
):
    drive_cycle = simple_test_cycle()
    simulation = ICEVehicleSimulation(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        powertrain=sample_ice_powertrain,
    )
    result = simulation.run()

    n = len(drive_cycle.time_s)
    assert len(result.engine_torque_nm) == n
    assert len(result.engine_rpm) == n
    assert len(result.fuel_power_w) == n


def test_ice_simulation_fuel_consumption_is_nonnegative(
    sample_vehicle, flat_environment, sample_ice_powertrain
):
    drive_cycle = simple_test_cycle()
    simulation = ICEVehicleSimulation(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        powertrain=sample_ice_powertrain,
    )
    result = simulation.run()

    assert result.total_fuel_energy_j >= 0
    assert result.total_fuel_volume_l >= 0


def test_ice_simulation_summary_contains_expected_keys(
    sample_vehicle, flat_environment, sample_ice_powertrain
):
    drive_cycle = simple_test_cycle()
    simulation = ICEVehicleSimulation(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        powertrain=sample_ice_powertrain,
    )
    result = simulation.run()
    summary = result.summary()

    expected_keys = {
        "distance_km",
        "max_speed_kmh",
        "peak_engine_torque_nm",
        "peak_engine_power_kw",
        "max_engine_rpm",
        "total_fuel_volume_l",
        "avg_fuel_consumption_l_per_100km",
    }
    assert expected_keys.issubset(summary.keys())