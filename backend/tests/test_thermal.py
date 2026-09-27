"""
Tests for Phase 5 - lumped thermal model and battery thermal tracking.
"""

import pytest

from app.physics.thermal import ThermalParams, ThermalState
from app.models.battery import Battery, BatteryState


def test_thermal_state_heats_up_under_constant_loss():
    params = ThermalParams(
        thermal_capacitance_j_per_k=5000.0,
        heat_transfer_coefficient_w_per_k=10.0,
        ambient_temp_c=25.0,
        initial_temp_c=25.0,
    )
    state = ThermalState(params)

    result = state.step(power_loss_w=500.0, dt_s=1.0)
    assert result["temperature_c"] > 25.0


def test_thermal_state_cools_towards_ambient_with_zero_loss():
    params = ThermalParams(
        thermal_capacitance_j_per_k=5000.0,
        heat_transfer_coefficient_w_per_k=10.0,
        ambient_temp_c=25.0,
        initial_temp_c=60.0,
    )
    state = ThermalState(params)

    for _ in range(100):
        result = state.step(power_loss_w=0.0, dt_s=1.0)

    assert result["temperature_c"] < 60.0
    assert result["temperature_c"] > 25.0  # not yet fully cooled after 100s


def test_battery_without_thermal_params_skips_temperature_tracking():
    battery = Battery(capacity_wh=1000.0)
    state = BatteryState(battery)

    result = state.step(battery_power_w=500.0, dt_s=1.0)
    assert result["temperature_c"] is None
    assert result["over_temp"] is None


def test_battery_with_thermal_params_tracks_temperature():
    thermal = ThermalParams(
        thermal_capacitance_j_per_k=20000.0,
        heat_transfer_coefficient_w_per_k=5.0,
        ambient_temp_c=25.0,
        initial_temp_c=25.0,
    )
    battery = Battery(capacity_wh=1000.0, thermal=thermal)
    state = BatteryState(battery)

    result = state.step(battery_power_w=2000.0, dt_s=1.0)
    assert result["temperature_c"] is not None
    assert result["temperature_c"] > 25.0