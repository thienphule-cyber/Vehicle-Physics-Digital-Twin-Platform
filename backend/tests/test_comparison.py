"""
Tests for Phase 8 - comparative analysis across powertrains.
"""

import pytest

from app.models.vehicle import Vehicle
from app.models.ice import ICEPowertrain
from app.models.motor import Motor
from app.models.battery import Battery
from app.models.bev import BEVPowertrain
from app.models.hybrid import HybridPowertrain
from app.physics.longitudinal import Environment
from app.physics.energy import GASOLINE_LHV_J_PER_L
from app.analysis.comparison import run_comparison
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
    return Environment()


@pytest.fixture
def ice_powertrain() -> ICEPowertrain:
    return ICEPowertrain(
        max_torque_nm=250.0,
        max_power_w=110_000.0,
        gear_ratio=3.5,
        final_drive_ratio=3.9,
        transmission_efficiency=0.92,
        engine_efficiency=0.30,
        fuel_lhv_j_per_l=GASOLINE_LHV_J_PER_L,
    )


@pytest.fixture
def motor() -> Motor:
    return Motor(
        max_torque_nm=300.0,
        max_power_w=150_000.0,
        gear_ratio=9.0,
        final_drive_ratio=1.0,
    )


@pytest.fixture
def bev_powertrain(motor) -> BEVPowertrain:
    battery = Battery(capacity_wh=60_000.0, initial_soc=0.8)
    return BEVPowertrain(motor=motor, battery=battery)


@pytest.fixture
def hybrid_powertrain(ice_powertrain, motor) -> HybridPowertrain:
    battery = Battery(capacity_wh=1500.0, initial_soc=0.6)
    return HybridPowertrain(ice=ice_powertrain, motor=motor, battery=battery)


def test_run_comparison_returns_matching_time_length(
    sample_vehicle, flat_environment, ice_powertrain, hybrid_powertrain, bev_powertrain
):
    drive_cycle = simple_test_cycle()

    result = run_comparison(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        ice_powertrain=ice_powertrain,
        hybrid_powertrain=hybrid_powertrain,
        bev_powertrain=bev_powertrain,
    )

    n = len(drive_cycle.time_s)
    assert len(result.time_s) == n
    assert len(result.ice_result["engine_torque_nm"]) == n
    assert len(result.bev_result["soc"]) == n


def test_run_comparison_all_powertrains_cover_same_distance(
    sample_vehicle, flat_environment, ice_powertrain, hybrid_powertrain, bev_powertrain
):
    drive_cycle = simple_test_cycle()

    result = run_comparison(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        ice_powertrain=ice_powertrain,
        hybrid_powertrain=hybrid_powertrain,
        bev_powertrain=bev_powertrain,
    )

    distances = result.comparison_table["distance_km"]
    # Same drive cycle for all three -> distance should be identical
    # (the wheel-following assumption means speed profile is the same).
    assert distances["ice"] == pytest.approx(distances["hybrid"], rel=1e-6)
    assert distances["ice"] == pytest.approx(distances["bev"], rel=1e-6)


def test_run_comparison_bev_has_no_fuel_and_ice_has_no_soc(
    sample_vehicle, flat_environment, ice_powertrain, hybrid_powertrain, bev_powertrain
):
    drive_cycle = simple_test_cycle()

    result = run_comparison(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        ice_powertrain=ice_powertrain,
        hybrid_powertrain=hybrid_powertrain,
        bev_powertrain=bev_powertrain,
    )

    table = result.comparison_table
    assert table["fuel_used_l"]["bev"] == 0.0
    assert table["final_soc_pct"]["ice"] is None


def test_run_comparison_table_contains_expected_metrics(
    sample_vehicle, flat_environment, ice_powertrain, hybrid_powertrain, bev_powertrain
):
    drive_cycle = simple_test_cycle()

    result = run_comparison(
        vehicle=sample_vehicle,
        environment=flat_environment,
        drive_cycle=drive_cycle,
        ice_powertrain=ice_powertrain,
        hybrid_powertrain=hybrid_powertrain,
        bev_powertrain=bev_powertrain,
    )

    expected_metrics = {
        "distance_km",
        "max_speed_kmh",
        "overall_efficiency_pct",
        "fuel_used_l",
        "energy_used_kwh",
        "regen_energy_kwh",
        "final_soc_pct",
    }
    assert expected_metrics.issubset(result.comparison_table.keys())

    for metric_values in result.comparison_table.values():
        assert set(metric_values.keys()) == {"ice", "hybrid", "bev"}