"""
Comparative analysis across powertrains.

Runs ICE, Hybrid and BEV simulations under identical conditions
(same vehicle body, environment, and drive cycle) and produces a
side-by-side comparison. This is the core "controlled experiment"
capability of the platform: it isolates the effect of powertrain
choice alone, since every other physical parameter is held constant.
"""

from dataclasses import dataclass

import numpy as np

from app.models.vehicle import Vehicle
from app.models.ice import ICEPowertrain
from app.models.motor import Motor
from app.models.battery import Battery
from app.models.bev import BEVPowertrain
from app.models.hybrid import HybridPowertrain
from app.physics.longitudinal import Environment, traction_force
from app.simulation.drive_cycle import DriveCycle
from app.simulation.ice_simulation import ICEVehicleSimulation
from app.simulation.bev_simulation import BEVVehicleSimulation
from app.simulation.hybrid_simulation import HybridVehicleSimulation
from app.analysis.metrics import (
    energy_breakdown_ice,
    energy_breakdown_bev,
    energy_breakdown_hybrid,
)


def _wheel_power_series(
    vehicle: Vehicle, environment: Environment, drive_cycle: DriveCycle
) -> np.ndarray:
    """Recompute wheel power time-series (identical for every powertrain,
    since it depends only on the shared vehicle body and drive cycle)."""
    n = len(drive_cycle.time_s)
    wheel_p = np.zeros(n)
    for i in range(n):
        v = float(drive_cycle.speed_mps[i])
        a = float(drive_cycle.acceleration_mps2[i])
        f = traction_force(vehicle, environment, v, a)
        wheel_p[i] = f * v
    return wheel_p


@dataclass
class ComparisonResult:
    """
    Full comparison output: per-powertrain time-series plus a unified
    scalar comparison table.
    """

    time_s: list
    ice_result: dict
    hybrid_result: dict
    bev_result: dict
    comparison_table: dict


def run_comparison(
    vehicle: Vehicle,
    environment: Environment,
    drive_cycle: DriveCycle,
    ice_powertrain: ICEPowertrain,
    hybrid_powertrain: HybridPowertrain,
    bev_powertrain: BEVPowertrain,
) -> ComparisonResult:
    """
    Run ICE, Hybrid and BEV simulations under the same vehicle body,
    environment and drive cycle, and build a unified comparison.
    """
    wheel_power = _wheel_power_series(vehicle, environment, drive_cycle)

    # ---------- ICE ----------
    ice_sim = ICEVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=ice_powertrain
    )
    ice_result = ice_sim.run()
    ice_energy = energy_breakdown_ice(
        time_s=ice_result.time_s,
        fuel_power_w=ice_result.fuel_power_w,
        engine_power_w=ice_result.engine_power_w,
        wheel_power_w=wheel_power,
    )

    # ---------- Hybrid ----------
    hybrid_sim = HybridVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=hybrid_powertrain
    )
    hybrid_result = hybrid_sim.run()
    hybrid_energy = energy_breakdown_hybrid(
        time_s=hybrid_result.time_s,
        fuel_power_w=hybrid_result.fuel_power_w,
        battery_power_w=hybrid_result.battery_power_w,
        ice_power_w=hybrid_result.ice_power_w,
        motor_power_w=hybrid_result.motor_power_w,
        wheel_power_w=wheel_power,
    )

    # ---------- BEV ----------
    bev_sim = BEVVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=bev_powertrain
    )
    bev_result = bev_sim.run()
    bev_energy = energy_breakdown_bev(
        time_s=bev_result.time_s,
        battery_power_w=bev_result.battery_power_w,
        motor_power_w=bev_result.motor_power_w,
        wheel_power_w=wheel_power,
    )

    ice_summary = ice_result.summary()
    hybrid_summary = hybrid_result.summary()
    bev_summary = bev_result.summary()

    comparison_table = {
        "distance_km": {
            "ice": ice_summary["distance_km"],
            "hybrid": hybrid_summary["distance_km"],
            "bev": bev_summary["distance_km"],
        },
        "max_speed_kmh": {
            "ice": ice_summary["max_speed_kmh"],
            "hybrid": hybrid_summary["max_speed_kmh"],
            "bev": bev_summary["max_speed_kmh"],
        },
        "overall_efficiency_pct": {
            "ice": ice_energy["overall_efficiency_pct"],
            "hybrid": hybrid_energy["overall_efficiency_pct"],
            "bev": bev_energy["overall_efficiency_pct"],
        },
        "fuel_used_l": {
            "ice": ice_summary["total_fuel_volume_l"],
            "hybrid": hybrid_summary["total_fuel_volume_l"],
            "bev": 0.0,
        },
        "energy_used_kwh": {
            "ice": 0.0,
            "hybrid": hybrid_energy["battery_discharge_energy_kwh"],
            "bev": bev_energy["battery_discharge_energy_kwh"],
        },
        "regen_energy_kwh": {
            "ice": 0.0,
            "hybrid": hybrid_energy["regen_energy_kwh"],
            "bev": bev_energy["regen_energy_kwh"],
        },
        "final_soc_pct": {
            "ice": None,
            "hybrid": hybrid_summary["final_soc_pct"],
            "bev": bev_summary["final_soc_pct"],
        },
    }

    return ComparisonResult(
        time_s=drive_cycle.time_s.tolist(),
        ice_result={
            "engine_torque_nm": ice_result.engine_torque_nm.tolist(),
            "engine_power_w": ice_result.engine_power_w.tolist(),
            "fuel_power_w": ice_result.fuel_power_w.tolist(),
            "summary": ice_summary,
            "energy_breakdown": ice_energy,
        },
        hybrid_result={
            "ice_torque_nm": hybrid_result.ice_torque_nm.tolist(),
            "motor_torque_nm": hybrid_result.motor_torque_nm.tolist(),
            "battery_power_w": hybrid_result.battery_power_w.tolist(),
            "soc": hybrid_result.soc.tolist(),
            "summary": hybrid_summary,
            "energy_breakdown": hybrid_energy,
        },
        bev_result={
            "motor_torque_nm": bev_result.motor_torque_nm.tolist(),
            "battery_power_w": bev_result.battery_power_w.tolist(),
            "soc": bev_result.soc.tolist(),
            "summary": bev_summary,
            "energy_breakdown": bev_energy,
        },
        comparison_table=comparison_table,
    )