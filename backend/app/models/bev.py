"""
BEV (battery electric vehicle) powertrain model.

Combines a Motor and a Battery into a single powertrain: given a
wheel torque demand and wheel angular velocity, computes motor state
and steps the battery SOC forward by one timestep.
"""

from dataclasses import dataclass

from app.models.motor import Motor
from app.models.battery import Battery, BatteryState


@dataclass
class BEVPowertrain:
    """
    A BEV powertrain: a single motor drawing from a single battery.
    """

    motor: Motor
    battery: Battery

    def create_state(self) -> "BEVPowertrainState":
        """Create a fresh mutable state tracker for a simulation run."""
        return BEVPowertrainState(self)


class BEVPowertrainState:
    """Mutable state (battery SOC) for a BEV powertrain over a simulation run."""

    def __init__(self, powertrain: BEVPowertrain) -> None:
        self.powertrain = powertrain
        self.battery_state = BatteryState(powertrain.battery)

    def step(self, wheel_torque_nm: float, wheel_omega_rad_s: float, dt_s: float) -> dict:
        """
        Advance the BEV powertrain by one timestep.

        Returns a dict combining motor output and updated battery SOC.
        """
        motor_result = self.powertrain.motor.calculate(wheel_torque_nm, wheel_omega_rad_s)
        battery_result = self.battery_state.step(motor_result["battery_power_w"], dt_s)

        return {
            **motor_result,
            "soc": battery_result["soc"],
            "battery_power_limited": battery_result["power_limited"],
        }