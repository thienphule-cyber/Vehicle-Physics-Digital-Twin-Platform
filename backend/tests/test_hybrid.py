"""
Tests for Phase 4 - Hybrid powertrain model and simulation.
"""

import pytest

from app.models.vehicle import Vehicle
from app.models.ice import ICEPowertrain
from app.models.motor import Motor
from app.models.battery import Battery
from app.models.hybrid import HybridPowertrain
from app.physics.longitudinal import Environment
from app.physics.energy import GASOLINE_LHV_J_PER_L
from app.simulation.hybrid_simulation import HybridVehicleSimulation
from app.simulation.standard_cycles import simple_test_cycle


@pytest.fixture
def sample_vehicle() -> Vehicle:
    return Vehicle(
        mass=1700.0,
        wheel_radius=0.34,
        drag_coefficient=0.28,
        frontal_area=2.2,
        rolling_resistance_coefficient=0.011,
    )


@pytest.fixture
def flat_environment() -> Environment:
    return Environment()


@pytest.fixture
def sample_hybrid_powertrain() -> HybridPowertrain:
    ice = ICEPowertrain(
        max_torque_nm=180.0,
        max_power_w=90_000.0,
        gear_ratio=3.5,
        final_drive_ratio=3.9,
        transmission_efficiency=0.92,
        engine_efficiency=0.32,
        fuel_lhv_j_per_l=GASOLINE_LHV_J_PER_L,
    )
    motor = Motor(
        max_torque_nm=150.0,
        max_power_w=50_000.0,
        gear_ratio=3.5,
        final_drive_ratio=3.9,
    )
    battery = Battery(capacity_wh=1500.0, initial_soc=0.6)

    return HybridPowertrain(ice=ice, motor=motor, battery=battery)


def test_hybrid_low_demand_uses_electric_only(sample_hybrid_powertrain):
    state = sample_hybrid_powertrain.create_state()

    # Small wheel torque -> should be below electric_only_power_threshold_w
    result = state.step(wheel_torque_nm=20.0, wheel_omega_rad_s=10.0, dt_s=1.0)

    assert result["ice_torque_nm"] == pytest.approx(0.0, abs=1e-6)
    assert abs(result["motor_torque_nm"]) > 0


def test_hybrid_high_demand_uses_ice_and_motor(sample_hybrid_powertrain):
    state = sample_hybrid_powertrain.create_state()

    # Large wheel torque at high speed -> high power demand -> ICE should engage
    result = state.step(wheel_torque_nm=300.0, wheel_omega_rad_s=100.0, dt_s=1.0)

    assert result["ice_torque_nm"] > 0
    assert result["fuel_power_w"] > 0


def test_hybrid_braking_uses_regen_only(sample_hybrid_powertrain):
    state = sample_hybrid_powertrain.create_state()

    result = state.step(wheel_torque_nm=-100.0, wheel_omega_rad_s=50.0, dt_s=1.0)

    assert result["ice_torque_nm"] == pytest.approx(0.0, abs=1e-6)
    assert result["battery_power_w"] < 0


def test_hybrid_simulation_runs_and_returns_matching_length_arrays(
    sample_vehicle, flat_environment, sample_hybrid_powertrain
):
    drive_cycle = simple_test_cycle()

    simulation = HybridVehicleSimulation(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        powertrain=sample_hybrid_powertrain,
    )
    result = simulation.run()

    n = len(drive_cycle.time_s)
    assert len(result.ice_torque_nm) == n
    assert len(result.motor_torque_nm) == n
    assert len(result.soc) == n


def test_hybrid_simulation_summary_contains_expected_keys(
    sample_vehicle, flat_environment, sample_hybrid_powertrain
):
    drive_cycle = simple_test_cycle()

    simulation = HybridVehicleSimulation(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        powertrain=sample_hybrid_powertrain,
    )
    result = simulation.run()
    summary = result.summary()

    expected_keys = {
        "distance_km",
        "max_speed_kmh",
        "peak_ice_torque_nm",
        "peak_motor_torque_nm",
        "final_soc_pct",
        "total_fuel_volume_l",
        "regen_energy_kwh",
        "avg_fuel_consumption_l_per_100km",
    }
    assert expected_keys.issubset(summary.keys())