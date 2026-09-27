"""
Energy analysis metrics.

Computes an energy flow breakdown (input energy, useful mechanical
energy, and losses per stage) from simulation time-series data. This
turns raw simulation output into an engineering-readable energy
balance, independent of which powertrain produced it.
"""

import numpy as np


def integrate_power(power_w: np.ndarray, time_s: np.ndarray) -> float:
    """
    Integrate a power time-series into total energy [J] using the
    trapezoidal rule. Negative power values (e.g. regen) are included
    as-is; callers should clip beforehand if they want only positive
    or only negative contributions.
    """
    return float(np.trapezoid(power_w, time_s))


def energy_breakdown_ice(
    time_s: np.ndarray,
    fuel_power_w: np.ndarray,
    engine_power_w: np.ndarray,
    wheel_power_w: np.ndarray,
) -> dict:
    """
    Energy breakdown for an ICE vehicle:

        Fuel energy -> Engine mechanical energy -> Wheel energy

    Returns energies in kWh and stage efficiencies in percent.
    """
    fuel_energy_j = integrate_power(fuel_power_w, time_s)
    engine_energy_j = integrate_power(np.clip(engine_power_w, 0, None), time_s)
    wheel_energy_j = integrate_power(np.clip(wheel_power_w, 0, None), time_s)

    engine_efficiency_pct = (
        (engine_energy_j / fuel_energy_j) * 100.0 if fuel_energy_j > 0 else 0.0
    )
    transmission_efficiency_pct = (
        (wheel_energy_j / engine_energy_j) * 100.0 if engine_energy_j > 0 else 0.0
    )
    overall_efficiency_pct = (
        (wheel_energy_j / fuel_energy_j) * 100.0 if fuel_energy_j > 0 else 0.0
    )

    return {
        "fuel_energy_kwh": fuel_energy_j / 3.6e6,
        "engine_mechanical_energy_kwh": engine_energy_j / 3.6e6,
        "wheel_energy_kwh": wheel_energy_j / 3.6e6,
        "engine_efficiency_pct": engine_efficiency_pct,
        "transmission_efficiency_pct": transmission_efficiency_pct,
        "overall_efficiency_pct": overall_efficiency_pct,
    }


def energy_breakdown_bev(
    time_s: np.ndarray,
    battery_power_w: np.ndarray,
    motor_power_w: np.ndarray,
    wheel_power_w: np.ndarray,
) -> dict:
    """
    Energy breakdown for a BEV:

        Battery discharge energy -> Motor mechanical energy -> Wheel energy
        (plus regenerated energy returned to the battery during braking)
    """
    discharge_energy_j = integrate_power(np.clip(battery_power_w, 0, None), time_s)
    regen_energy_j = -integrate_power(np.clip(battery_power_w, None, 0), time_s)
    motor_energy_j = integrate_power(np.clip(motor_power_w, 0, None), time_s)
    wheel_energy_j = integrate_power(np.clip(wheel_power_w, 0, None), time_s)

    motor_efficiency_pct = (
        (motor_energy_j / discharge_energy_j) * 100.0 if discharge_energy_j > 0 else 0.0
    )
    overall_efficiency_pct = (
        (wheel_energy_j / discharge_energy_j) * 100.0 if discharge_energy_j > 0 else 0.0
    )

    return {
        "battery_discharge_energy_kwh": discharge_energy_j / 3.6e6,
        "regen_energy_kwh": regen_energy_j / 3.6e6,
        "motor_mechanical_energy_kwh": motor_energy_j / 3.6e6,
        "wheel_energy_kwh": wheel_energy_j / 3.6e6,
        "motor_efficiency_pct": motor_efficiency_pct,
        "overall_efficiency_pct": overall_efficiency_pct,
    }


def energy_breakdown_hybrid(
    time_s: np.ndarray,
    fuel_power_w: np.ndarray,
    battery_power_w: np.ndarray,
    ice_power_w: np.ndarray,
    motor_power_w: np.ndarray,
    wheel_power_w: np.ndarray,
) -> dict:
    """
    Energy breakdown for a Hybrid: combines fuel and battery energy
    sources into one wheel-energy result.
    """
    fuel_energy_j = integrate_power(fuel_power_w, time_s)
    discharge_energy_j = integrate_power(np.clip(battery_power_w, 0, None), time_s)
    regen_energy_j = -integrate_power(np.clip(battery_power_w, None, 0), time_s)

    ice_mech_energy_j = integrate_power(np.clip(ice_power_w, 0, None), time_s)
    motor_mech_energy_j = integrate_power(np.clip(motor_power_w, 0, None), time_s)
    wheel_energy_j = integrate_power(np.clip(wheel_power_w, 0, None), time_s)

    total_input_energy_j = fuel_energy_j + discharge_energy_j
    overall_efficiency_pct = (
        (wheel_energy_j / total_input_energy_j) * 100.0
        if total_input_energy_j > 0
        else 0.0
    )

    return {
        "fuel_energy_kwh": fuel_energy_j / 3.6e6,
        "battery_discharge_energy_kwh": discharge_energy_j / 3.6e6,
        "regen_energy_kwh": regen_energy_j / 3.6e6,
        "ice_mechanical_energy_kwh": ice_mech_energy_j / 3.6e6,
        "motor_mechanical_energy_kwh": motor_mech_energy_j / 3.6e6,
        "wheel_energy_kwh": wheel_energy_j / 3.6e6,
        "overall_efficiency_pct": overall_efficiency_pct,
    }