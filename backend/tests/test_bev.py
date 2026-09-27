"""
Tests for Phase 4 - BEV powertrain model and simulation.
"""

import pytest

from app.models.vehicle import Vehicle
from app.models.motor import Motor
from app.models.battery import Battery
from app.models.bev import BEVPowertrain
from app.physics.longitudinal import Environment
from app.simulation.bev_simulation import BEVVehicleSimulation
from app.simulation.standard_cycles import simple_test_cycle


@pytest.fixture
def sample_vehicle() -> Vehicle:
    return Vehicle(
        mass=1800.0,
        wheel_radius=0.34,
        drag_coefficient=0.28,
        frontal_area=2.3,
        rolling_resistance_coefficient=0.010,
    )


@pytest.fixture
def flat_environment() -> Environment:
    return Environment()


@pytest.fixture
def sample_motor() -> Motor:
    return Motor(
        max_torque_nm=300.0,
        max_power_w=150_000.0,
        gear_ratio=9.0,
        final_drive_ratio=1.0,
    )


@pytest.fixture
def sample_battery() -> Battery:
    return Battery(capacity_wh=60_000.0, initial_soc=0.8)


def test_bev_powertrain_regen_charges_battery(sample_motor, sample_battery):
    powertrain = BEVPowertrain(motor=sample_motor, battery=sample_battery)
    state = powertrain.create_state()

    # Negative wheel torque (braking) at nonzero speed -> regen -> SOC should increase
    initial_soc = state.battery_state.soc
    result = state.step(wheel_torque_nm=-200.0, wheel_omega_rad_s=50.0, dt_s=1.0)

    assert result["battery_power_w"] < 0
    assert result["soc"] >= initial_soc


def test_bev_powertrain_driving_discharges_battery(sample_motor, sample_battery):
    powertrain = BEVPowertrain(motor=sample_motor, battery=sample_battery)
    state = powertrain.create_state()

    initial_soc = state.battery_state.soc
    result = state.step(wheel_torque_nm=200.0, wheel_omega_rad_s=50.0, dt_s=1.0)

    assert result["battery_power_w"] > 0
    assert result["soc"] <= initial_soc


def test_bev_simulation_runs_and_soc_stays_in_bounds(
    sample_vehicle, flat_environment, sample_motor, sample_battery
):
    drive_cycle = simple_test_cycle()
    powertrain = BEVPowertrain(motor=sample_motor, battery=sample_battery)

    simulation = BEVVehicleSimulation(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        powertrain=powertrain,
    )
    result = simulation.run()

    assert len(result.soc) == len(drive_cycle.time_s)
    assert (result.soc >= sample_battery.min_soc - 1e-6).all()
    assert (result.soc <= sample_battery.max_soc + 1e-6).all()


def test_bev_simulation_summary_contains_expected_keys(
    sample_vehicle, flat_environment, sample_motor, sample_battery
):
    drive_cycle = simple_test_cycle()
    powertrain = BEVPowertrain(motor=sample_motor, battery=sample_battery)

    simulation = BEVVehicleSimulation(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        powertrain=powertrain,
    )
    result = simulation.run()
    summary = result.summary()

    expected_keys = {
        "distance_km",
        "max_speed_kmh",
        "peak_motor_torque_nm",
        "peak_motor_power_kw",
        "final_soc_pct",
        "total_energy_kwh",
        "regen_energy_kwh",
        "avg_consumption_kwh_per_100km",
    }
    assert expected_keys.issubset(summary.keys())