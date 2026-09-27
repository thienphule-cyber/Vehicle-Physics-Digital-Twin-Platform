"""
Validation-related API endpoints.

Phase 7: upload real-world vehicle data (CSV), preview it, and run a
powertrain simulation driven by the real data's speed profile, then
compare a model-predicted quantity (SOC or cumulative fuel volume)
against the corresponding real measured column.
"""

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.analysis.validation import compare_series
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
)
from app.models.bev import BEVPowertrain
from app.simulation.bev_simulation import BEVVehicleSimulation
from app.simulation.ice_simulation import ICEVehicleSimulation
from app.simulation.real_data import parse_real_data_csv, preview_real_data
from app.physics.energy import fuel_energy_to_volume

router = APIRouter(prefix="/api/validation", tags=["validation"])


# ---------- Upload & preview ----------

class UploadCsvRequest(BaseModel):
    csv_text: str
    source_name: str = "uploaded_data"


@router.post("/upload")
def upload_real_data(payload: UploadCsvRequest) -> dict:
    """
    Parse an uploaded CSV (sent as raw text) and return a preview,
    including which reference columns (soc, fuel_l) are available for
    validation.
    """
    try:
        data = parse_real_data_csv(payload.csv_text, source_name=payload.source_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return preview_real_data(data)


# ---------- BEV validation (model SOC vs real SOC) ----------

class ValidateBEVRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    motor: MotorParams
    battery: BatteryParams
    csv_text: str
    source_name: str = "uploaded_data"


@router.post("/validate-bev")
def validate_bev(payload: ValidateBEVRequest) -> dict:
    """
    Run a BEV simulation using the uploaded real data's speed profile
    as the drive cycle, then compare model SOC against the real 'soc'
    column (required in the CSV for this endpoint).
    """
    try:
        real_data = parse_real_data_csv(payload.csv_text, source_name=payload.source_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not real_data.has_reference("soc"):
        raise HTTPException(
            status_code=400,
            detail="CSV must contain a 'soc' column to validate a BEV model.",
        )

    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = real_data.to_drive_cycle()

    motor = _build_motor(payload.motor)
    battery = _build_battery(payload.battery)
    powertrain = BEVPowertrain(motor=motor, battery=battery)

    simulation = BEVVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=powertrain
    )
    result = simulation.run()

    comparison = compare_series(
        model_time_s=result.time_s,
        model_values=result.soc,
        real_time_s=real_data.time_s,
        real_values=real_data.get_reference("soc"),
    )

    return {
        "quantity": "soc",
        "comparison": comparison,
        "model_summary": result.summary(),
    }


# ---------- ICE validation (model cumulative fuel vs real cumulative fuel) ----------

class ValidateICERequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    powertrain: ICEPowertrainParams
    csv_text: str
    source_name: str = "uploaded_data"


@router.post("/validate-ice")
def validate_ice(payload: ValidateICERequest) -> dict:
    """
    Run an ICE simulation using the uploaded real data's speed profile
    as the drive cycle, then compare model cumulative fuel volume
    against the real 'fuel_l' column (required in the CSV, assumed to
    already be cumulative liters consumed).
    """
    try:
        real_data = parse_real_data_csv(payload.csv_text, source_name=payload.source_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not real_data.has_reference("fuel_l"):
        raise HTTPException(
            status_code=400,
            detail="CSV must contain a 'fuel_l' column to validate an ICE model.",
        )

    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = real_data.to_drive_cycle()
    powertrain = _build_ice_powertrain(payload.powertrain)

    simulation = ICEVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=powertrain
    )
    result = simulation.run()

    # Build cumulative fuel volume time-series from fuel_power_w
    cumulative_fuel_l = np.zeros(len(result.time_s))
    for i in range(1, len(result.time_s)):
        dt = result.time_s[i] - result.time_s[i - 1]
        avg_power = (result.fuel_power_w[i] + result.fuel_power_w[i - 1]) / 2.0
        energy_j = avg_power * dt
        cumulative_fuel_l[i] = cumulative_fuel_l[i - 1] + fuel_energy_to_volume(
            energy_j, powertrain.fuel_lhv_j_per_l
        )

    comparison = compare_series(
        model_time_s=result.time_s,
        model_values=cumulative_fuel_l,
        real_time_s=real_data.time_s,
        real_values=real_data.get_reference("fuel_l"),
    )

    return {
        "quantity": "cumulative_fuel_l",
        "comparison": comparison,
        "model_summary": result.summary(),
    }