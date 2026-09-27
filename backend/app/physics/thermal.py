"""
Lumped thermal model.

A lumped-parameter thermal model treats a component (battery, motor,
engine) as a single thermal mass exchanging heat with the ambient
environment through convective cooling:

    C_th * dT/dt = P_loss - h*A*(T - T_amb)

This is a first-order ODE, integrated here with simple forward Euler
per timestep (consistent with the rest of the simulation engine,
which already uses fixed timestep integration).
"""

from dataclasses import dataclass


@dataclass
class ThermalParams:
    """
    Parameters for a lumped thermal model of one component.

    Attributes:
        thermal_capacitance_j_per_k: Effective thermal mass C_th [J/K]
        heat_transfer_coefficient_w_per_k: Combined h*A cooling
            coefficient [W/K]
        ambient_temp_c: Ambient temperature [°C]
        initial_temp_c: Initial component temperature [°C]
        max_safe_temp_c: Temperature above which the component is
            considered thermally limited (used for warnings /
            derating in later phases)
    """

    thermal_capacitance_j_per_k: float
    heat_transfer_coefficient_w_per_k: float
    ambient_temp_c: float = 25.0
    initial_temp_c: float = 25.0
    max_safe_temp_c: float = 85.0

    def __post_init__(self) -> None:
        if self.thermal_capacitance_j_per_k <= 0:
            raise ValueError("thermal_capacitance_j_per_k must be positive.")
        if self.heat_transfer_coefficient_w_per_k <= 0:
            raise ValueError("heat_transfer_coefficient_w_per_k must be positive.")


class ThermalState:
    """
    Mutable temperature tracker for one component, stepped forward
    in time using the lumped thermal model.
    """

    def __init__(self, params: ThermalParams) -> None:
        self.params = params
        self.temperature_c = params.initial_temp_c

    def step(self, power_loss_w: float, dt_s: float) -> dict:
        """
        Advance temperature by one timestep given the heat generated
        by the component (power_loss_w, always >= 0).

        Forward Euler integration:
            dT = (P_loss - h*A*(T - T_amb)) / C_th * dt

        Returns a dict with:
            temperature_c: updated temperature
            over_temp: True if temperature exceeds max_safe_temp_c
        """
        cooling_w = self.params.heat_transfer_coefficient_w_per_k * (
            self.temperature_c - self.params.ambient_temp_c
        )
        d_temp = (power_loss_w - cooling_w) / self.params.thermal_capacitance_j_per_k * dt_s

        self.temperature_c += d_temp

        return {
            "temperature_c": self.temperature_c,
            "over_temp": self.temperature_c > self.params.max_safe_temp_c,
        }