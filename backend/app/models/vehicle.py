"""
Vehicle model.

Defines the physical parameters of a vehicle body that are shared
across all powertrain types (ICE, Hybrid, BEV). This class only
describes the mechanical/aerodynamic properties of the vehicle,
not the powertrain itself.
"""

from dataclasses import dataclass


@dataclass
class Vehicle:
    """
    Physical parameters of the vehicle body.

    Attributes:
        mass: Vehicle mass [kg]
        wheel_radius: Rolling radius of the wheel [m]
        drag_coefficient: Aerodynamic drag coefficient Cd [-]
        frontal_area: Frontal area A [m^2]
        rolling_resistance_coefficient: Rolling resistance coefficient Crr [-]
        num_wheels: Number of wheels (mainly for reference/UI, not used in core equations)
    """

    mass: float
    wheel_radius: float
    drag_coefficient: float
    frontal_area: float
    rolling_resistance_coefficient: float
    num_wheels: int = 4

    def __post_init__(self) -> None:
        if self.mass <= 0:
            raise ValueError("Vehicle mass must be positive.")
        if self.wheel_radius <= 0:
            raise ValueError("Wheel radius must be positive.")
        if self.frontal_area <= 0:
            raise ValueError("Frontal area must be positive.")
        if self.drag_coefficient < 0:
            raise ValueError("Drag coefficient cannot be negative.")
        if self.rolling_resistance_coefficient < 0:
            raise ValueError("Rolling resistance coefficient cannot be negative.")