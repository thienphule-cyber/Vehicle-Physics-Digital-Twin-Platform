"""
Battery model.

Tracks state of charge (SOC) and temperature over time given battery
power demand. Shared by Hybrid and BEV powertrains.

    SOC[k+1] = SOC[k] - (P_battery * dt) / E_battery

Positive P_battery = discharging (providing power to the motor).
Negative P_battery = charging (regenerative braking).

Phase 5 adds a lumped thermal model: a fraction of battery power is
assumed to be dissipated as heat (I^2R-type losses), raising the
battery temperature, which is tracked alongside SOC.
"""

from dataclasses import dataclass
from typing import Optional

from app.physics.thermal import ThermalParams, ThermalState


@dataclass
class Battery:
    """
    Parameters describing a battery pack.

    Attributes:
        capacity_wh: Usable energy capacity [Wh]
        initial_soc: Initial state of charge [0-1]
        min_soc: Minimum allowed SOC [0-1], used for saturation
        max_soc: Maximum allowed SOC [0-1], used for saturation
        internal_efficiency: Round-trip efficiency factor applied to
            charge/discharge power (simplified, V1 constant value)
        thermal: Optional thermal model parameters. If None, thermal
            tracking is skipped (backward compatible with Phase 4).
        heat_loss_fraction: Fraction of |battery_power| dissipated as
            heat (1 - internal_efficiency by default if not set)
    """

    capacity_wh: float
    initial_soc: float = 0.7
    min_soc: float = 0.1
    max_soc: float = 1.0
    internal_efficiency: float = 0.95
    thermal: Optional[ThermalParams] = None
    heat_loss_fraction: Optional[float] = None

    def __post_init__(self) -> None:
        if self.capacity_wh <= 0:
            raise ValueError("capacity_wh must be positive.")
        if not (0 <= self.min_soc < self.max_soc <= 1):
            raise ValueError("Require 0 <= min_soc < max_soc <= 1.")
        if not (self.min_soc <= self.initial_soc <= self.max_soc):
            raise ValueError("initial_soc must be within [min_soc, max_soc].")
        if not (0 < self.internal_efficiency <= 1):
            raise ValueError("internal_efficiency must be in (0, 1].")
        if self.heat_loss_fraction is None:
            self.heat_loss_fraction = 1.0 - self.internal_efficiency

    def capacity_j(self) -> float:
        """Battery capacity converted to Joules."""
        return self.capacity_wh * 3600.0


class BatteryState:
    """
    Mutable state tracker for a Battery over a simulation run.

    Kept separate from the Battery dataclass (which holds fixed
    parameters) so the same Battery config can be reused across
    multiple simulation runs without carrying stale state.
    """

    def __init__(self, battery: Battery) -> None:
        self.battery = battery
        self.soc = battery.initial_soc
        self.thermal_state: Optional[ThermalState] = (
            ThermalState(battery.thermal) if battery.thermal is not None else None
        )

    def step(self, battery_power_w: float, dt_s: float) -> dict:
        """
        Advance SOC (and temperature, if thermal params were given)
        by one timestep given battery power demand.

        Returns a dict with:
            soc: updated SOC after this step
            power_limited: True if SOC would have gone outside bounds
            temperature_c: updated temperature, or None if no thermal model
            over_temp: True if temperature exceeds max_safe_temp_c, or None
        """
        capacity_j = self.battery.capacity_j()

        if battery_power_w >= 0:
            energy_drawn_j = battery_power_w * dt_s / self.battery.internal_efficiency
        else:
            energy_drawn_j = battery_power_w * dt_s * self.battery.internal_efficiency

        delta_soc = -energy_drawn_j / capacity_j
        new_soc = self.soc + delta_soc

        power_limited = False
        if new_soc < self.battery.min_soc:
            new_soc = self.battery.min_soc
            power_limited = True
        elif new_soc > self.battery.max_soc:
            new_soc = self.battery.max_soc
            power_limited = True

        self.soc = new_soc

        temperature_c = None
        over_temp = None
        if self.thermal_state is not None:
            heat_loss_w = abs(battery_power_w) * self.battery.heat_loss_fraction
            thermal_result = self.thermal_state.step(heat_loss_w, dt_s)
            temperature_c = thermal_result["temperature_c"]
            over_temp = thermal_result["over_temp"]

        return {
            "soc": self.soc,
            "power_limited": power_limited,
            "temperature_c": temperature_c,
            "over_temp": over_temp,
        }