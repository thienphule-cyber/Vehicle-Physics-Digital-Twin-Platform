"""
Hybrid powertrain model.

Combines an ICE, a Motor and a Battery with a simple rule-based
energy management controller:

    - Low wheel power demand -> motor only (electric drive)
    - High wheel power demand -> ICE + motor together
    - Negative demand (braking) -> motor regeneration only

This is a V1 simplification. More advanced control strategies
(e.g. SOC-aware blending, optimal control) are a later-phase
improvement.
"""

from dataclasses import dataclass

from app.models.ice import ICEPowertrain
from app.models.motor import Motor
from app.models.battery import Battery, BatteryState


@dataclass
class HybridPowertrain:
    """
    A hybrid powertrain: ICE + electric motor sharing the wheel load,
    with a single battery.

    Attributes:
        ice: ICE powertrain (engine + transmission)
        motor: Electric motor (+ its own gear reduction)
        battery: Battery pack shared with the motor
        electric_only_power_threshold_w: Below this wheel power demand,
            drive using the motor alone (pure EV mode)
        motor_assist_fraction: Fraction of wheel power demand assigned
            to the motor when both ICE and motor are active together
    """

    ice: ICEPowertrain
    motor: Motor
    battery: Battery
    electric_only_power_threshold_w: float = 15_000.0
    motor_assist_fraction: float = 0.3

    def create_state(self) -> "HybridPowertrainState":
        return HybridPowertrainState(self)


class HybridPowertrainState:
    """Mutable state (battery SOC) for a hybrid powertrain over a simulation run."""

    def __init__(self, powertrain: HybridPowertrain) -> None:
        self.powertrain = powertrain
        self.battery_state = BatteryState(powertrain.battery)

    def step(self, wheel_torque_nm: float, wheel_omega_rad_s: float, dt_s: float) -> dict:
        """
        Advance the hybrid powertrain by one timestep using the
        rule-based controller described in the module docstring.
        """
        wheel_power_w = wheel_torque_nm * wheel_omega_rad_s
        pt = self.powertrain

        if wheel_power_w < 0:
            # Braking: motor handles regeneration, ICE contributes nothing.
            ice_torque_share = 0.0
            motor_torque_share = wheel_torque_nm
        elif wheel_power_w <= pt.electric_only_power_threshold_w:
            # Low demand: electric-only drive.
            ice_torque_share = 0.0
            motor_torque_share = wheel_torque_nm
        else:
            # High demand: split between motor (assist) and ICE (majority).
            motor_torque_share = wheel_torque_nm * pt.motor_assist_fraction
            ice_torque_share = wheel_torque_nm - motor_torque_share

        ice_result = pt.ice.calculate(ice_torque_share, wheel_omega_rad_s)
        motor_result = pt.motor.calculate(motor_torque_share, wheel_omega_rad_s)

        battery_result = self.battery_state.step(motor_result["battery_power_w"], dt_s)

        return {
            "wheel_power_w": wheel_power_w,
            "ice_torque_nm": ice_result["engine_torque_nm"],
            "ice_rpm": ice_result["engine_rpm"],
            "ice_power_w": ice_result["engine_power_w"],
            "fuel_power_w": ice_result["fuel_power_w"],
            "motor_torque_nm": motor_result["motor_torque_nm"],
            "motor_rpm": motor_result["motor_rpm"],
            "motor_power_w": motor_result["motor_power_w"],
            "battery_power_w": motor_result["battery_power_w"],
            "soc": battery_result["soc"],
            "battery_power_limited": battery_result["power_limited"],
        }