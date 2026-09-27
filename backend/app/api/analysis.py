"""
Analysis-related API endpoints.

Phase 5 exposes an endpoint that runs a powertrain simulation
(reusing the Phase 3/4 simulation engines) and returns an energy
flow breakdown instead of just raw time-series, so the frontend can
show where energy is lost at each conversion stage.
"""

import math

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.analysis.metrics import (
    energy_breakdown_ice,
    energy_breakdown_bev,
    energy_breakdown_hybrid,
)
from app.api.simulation import (
    VehicleParams,
    EnvironmentParams,
    ICEPowertrainParams,
    MotorParams,
    BatteryParams,
    _build_vehicle,
    _build_environment,
    _build_ice_powertrain,
    _build_motor,
    _build_battery,
    _get_drive_cycle,
)
from app.models.bev import BEVPowertrain
from app.models.hybrid import HybridPowertrain
from app.simulation.ice_simulation import ICEVehicleSimulation
from app.simulation.bev_simulation import BEVVehicleSimulation
from app.simulation.hybrid_simulation import HybridVehicleSimulation
from app.physics.longitudinal import traction_force, wheel_torque
from app.physics.drivetrain import wheel_angular_velocity
import numpy as np

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _wheel_power_series(vehicle, environment, drive_cycle) -> np.ndarray:
    """Recompute wheel power time-series (shared by all powertrains)."""
    n = len(drive_cycle.time_s)
    wheel_p = np.zeros(n)
    for i in range(n):
        v = float(drive_cycle.speed_mps[i])
        a = float(drive_cycle.acceleration_mps2[i])
        f = traction_force(vehicle, environment, v, a)
        wheel_p[i] = f * v
    return wheel_p


class ICEEnergyAnalysisRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    powertrain: ICEPowertrainParams
    drive_cycle_name: str = "simple_test_cycle"


@router.post("/energy-ice")
def analyze_ice_energy(payload: ICEEnergyAnalysisRequest) -> dict:
    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = _get_drive_cycle(payload.drive_cycle_name)
    powertrain = _build_ice_powertrain(payload.powertrain)

    simulation = ICEVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=powertrain
    )
    result = simulation.run()

    wheel_power = _wheel_power_series(vehicle, environment, drive_cycle)

    return energy_breakdown_ice(
        time_s=result.time_s,
        fuel_power_w=result.fuel_power_w,
        engine_power_w=result.engine_power_w,
        wheel_power_w=wheel_power,
    )


class BEVEnergyAnalysisRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    motor: MotorParams
    battery: BatteryParams
    drive_cycle_name: str = "simple_test_cycle"


@router.post("/energy-bev")
def analyze_bev_energy(payload: BEVEnergyAnalysisRequest) -> dict:
    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = _get_drive_cycle(payload.drive_cycle_name)

    motor = _build_motor(payload.motor)
    battery = _build_battery(payload.battery)
    powertrain = BEVPowertrain(motor=motor, battery=battery)

    simulation = BEVVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=powertrain
    )
    result = simulation.run()

    wheel_power = _wheel_power_series(vehicle, environment, drive_cycle)

    return energy_breakdown_bev(
        time_s=result.time_s,
        battery_power_w=result.battery_power_w,
        motor_power_w=result.motor_power_w,
        wheel_power_w=wheel_power,
    )


class HybridEnergyAnalysisRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    ice: ICEPowertrainParams
    motor: MotorParams
    battery: BatteryParams
    electric_only_power_threshold_w: float = 15_000.0
    motor_assist_fraction: float = Field(0.3, ge=0, le=1)
    drive_cycle_name: str = "simple_test_cycle"


@router.post("/energy-hybrid")
def analyze_hybrid_energy(payload: HybridEnergyAnalysisRequest) -> dict:
    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = _get_drive_cycle(payload.drive_cycle_name)

    ice = _build_ice_powertrain(payload.ice)
    motor = _build_motor(payload.motor)
    battery = _build_battery(payload.battery)

    powertrain = HybridPowertrain(
        ice=ice,
        motor=motor,
        battery=battery,
        electric_only_power_threshold_w=payload.electric_only_power_threshold_w,
        motor_assist_fraction=payload.motor_assist_fraction,
    )

    simulation = HybridVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=powertrain
    )
    result = simulation.run()

    wheel_power = _wheel_power_series(vehicle, environment, drive_cycle)

    return energy_breakdown_hybrid(
        time_s=result.time_s,
        fuel_power_w=result.fuel_power_w,
        battery_power_w=result.battery_power_w,
        ice_power_w=result.ice_power_w,
        motor_power_w=result.motor_power_w,
        wheel_power_w=wheel_power,
    )