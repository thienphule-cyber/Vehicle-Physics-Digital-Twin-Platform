"""
Tests for Phase 5 - energy analysis metrics.
"""

import numpy as np
import pytest

from app.analysis.metrics import (
    integrate_power,
    energy_breakdown_ice,
    energy_breakdown_bev,
)


def test_integrate_power_constant_power():
    time_s = np.array([0.0, 1.0, 2.0, 3.0])
    power_w = np.array([100.0, 100.0, 100.0, 100.0])

    energy_j = integrate_power(power_w, time_s)
    assert energy_j == pytest.approx(300.0, rel=1e-6)


def test_energy_breakdown_ice_efficiency_bounds():
    time_s = np.array([0.0, 1.0, 2.0])
    fuel_power_w = np.array([1000.0, 1000.0, 1000.0])
    engine_power_w = np.array([300.0, 300.0, 300.0])
    wheel_power_w = np.array([250.0, 250.0, 250.0])

    breakdown = energy_breakdown_ice(time_s, fuel_power_w, engine_power_w, wheel_power_w)

    assert 0 <= breakdown["engine_efficiency_pct"] <= 100
    assert 0 <= breakdown["overall_efficiency_pct"] <= 100
    assert breakdown["overall_efficiency_pct"] <= breakdown["engine_efficiency_pct"]


def test_energy_breakdown_bev_handles_zero_discharge():
    time_s = np.array([0.0, 1.0])
    battery_power_w = np.array([0.0, 0.0])
    motor_power_w = np.array([0.0, 0.0])
    wheel_power_w = np.array([0.0, 0.0])

    breakdown = energy_breakdown_bev(time_s, battery_power_w, motor_power_w, wheel_power_w)

    assert breakdown["motor_efficiency_pct"] == 0.0
    assert breakdown["overall_efficiency_pct"] == 0.0