"""
Comparison-related API endpoints.

Phase 8 exposes a single endpoint that runs ICE, Hybrid and BEV
simulations under identical conditions (same vehicle body,
environment and drive cycle) and returns a unified comparison,
enabling the platform's core "controlled experiment" use case.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.analysis.comparison import run_comparison
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

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


class RunComparisonRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    drive_cycle_name: str = "simple_test_cycle"

    ice: ICEPowertrainParams
    motor: MotorParams
    bev_battery: BatteryParams
    hybrid_battery: BatteryParams

    electric_only_power_threshold_w: float = 15_000.0
    motor_assist_fraction: float = Field(0.3, ge=0, le=1)


class RunComparisonResponse(BaseModel):
    time_s: list[float]
    ice_result: dict
    hybrid_result: dict
    bev_result: dict
    comparison_table: dict


@router.post("/run", response_model=RunComparisonResponse)
def run_comparison_endpoint(payload: RunComparisonRequest) -> RunComparisonResponse:
    """
    Run all three powertrains under the same vehicle body, environment
    and drive cycle, and return a unified comparison.
    """
    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = _get_drive_cycle(payload.drive_cycle_name)

    ice_powertrain = _build_ice_powertrain(payload.ice)
    motor = _build_motor(payload.motor)

    bev_battery = _build_battery(payload.bev_battery)
    bev_powertrain = BEVPowertrain(motor=motor, battery=bev_battery)

    hybrid_battery = _build_battery(payload.hybrid_battery)
    # Hybrid needs its own ICE instance (separate object, same params)
    # so that stateful attributes are never shared between simulations.
    hybrid_ice = _build_ice_powertrain(payload.ice)
    hybrid_motor = _build_motor(payload.motor)
    hybrid_powertrain = HybridPowertrain(
        ice=hybrid_ice,
        motor=hybrid_motor,
        battery=hybrid_battery,
        electric_only_power_threshold_w=payload.electric_only_power_threshold_w,
        motor_assist_fraction=payload.motor_assist_fraction,
    )

    result = run_comparison(
        vehicle=vehicle,
        environment=environment,
        drive_cycle=drive_cycle,
        ice_powertrain=ice_powertrain,
        hybrid_powertrain=hybrid_powertrain,
        bev_powertrain=bev_powertrain,
    )

    return RunComparisonResponse(
        time_s=result.time_s,
        ice_result=result.ice_result,
        hybrid_result=result.hybrid_result,
        bev_result=result.bev_result,
        comparison_table=result.comparison_table,
    )