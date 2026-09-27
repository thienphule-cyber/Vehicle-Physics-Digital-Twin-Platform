"""
Simulation-related API endpoints.

Phase 2: pure vehicle dynamics simulation (no powertrain).
Phase 3: ICE powertrain simulation.
Phase 4: BEV and Hybrid powertrain simulation.
"""

import math

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.vehicle import Vehicle
from app.models.ice import ICEPowertrain
from app.models.motor import Motor
from app.models.battery import Battery
from app.models.bev import BEVPowertrain
from app.models.hybrid import HybridPowertrain
from app.physics.longitudinal import Environment
from app.physics.energy import GASOLINE_LHV_J_PER_L, DIESEL_LHV_J_PER_L
from app.simulation.solver import VehicleDynamicsSimulation
from app.simulation.ice_simulation import ICEVehicleSimulation
from app.simulation.bev_simulation import BEVVehicleSimulation
from app.simulation.hybrid_simulation import HybridVehicleSimulation
from app.simulation.standard_cycles import simple_test_cycle

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


# ---------- Shared param models ----------

class VehicleParams(BaseModel):
    mass: float = Field(..., gt=0)
    wheel_radius: float = Field(..., gt=0)
    drag_coefficient: float = Field(..., ge=0)
    frontal_area: float = Field(..., gt=0)
    rolling_resistance_coefficient: float = Field(..., ge=0)


class EnvironmentParams(BaseModel):
    air_density: float = 1.225
    road_grade_deg: float = 0.0
    wind_speed: float = 0.0


AVAILABLE_DRIVE_CYCLES = {"simple_test_cycle": simple_test_cycle}
FUEL_LHV_BY_TYPE = {"gasoline": GASOLINE_LHV_J_PER_L, "diesel": DIESEL_LHV_J_PER_L}


def _build_vehicle(v: VehicleParams) -> Vehicle:
    return Vehicle(
        mass=v.mass,
        wheel_radius=v.wheel_radius,
        drag_coefficient=v.drag_coefficient,
        frontal_area=v.frontal_area,
        rolling_resistance_coefficient=v.rolling_resistance_coefficient,
    )


def _build_environment(e: EnvironmentParams) -> Environment:
    return Environment(
        air_density=e.air_density,
        road_grade_rad=math.radians(e.road_grade_deg),
        wind_speed=e.wind_speed,
    )


def _get_drive_cycle(name: str):
    if name not in AVAILABLE_DRIVE_CYCLES:
        raise HTTPException(status_code=404, detail=f"Unknown drive cycle: {name}")
    return AVAILABLE_DRIVE_CYCLES[name]()


@router.get("/drive-cycles")
def list_drive_cycles() -> list[str]:
    return list(AVAILABLE_DRIVE_CYCLES.keys())


# ---------- Phase 2: pure vehicle dynamics ----------

class RunSimulationRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    drive_cycle_name: str = "simple_test_cycle"


class RunSimulationResponse(BaseModel):
    time_s: list[float]
    velocity_mps: list[float]
    acceleration_mps2: list[float]
    f_traction_n: list[float]
    wheel_torque_nm: list[float]
    wheel_power_w: list[float]
    summary: dict


@router.post("/run", response_model=RunSimulationResponse)
def run_simulation(payload: RunSimulationRequest) -> RunSimulationResponse:
    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = _get_drive_cycle(payload.drive_cycle_name)

    simulation = VehicleDynamicsSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle
    )
    result = simulation.run()

    return RunSimulationResponse(
        time_s=result.time_s.tolist(),
        velocity_mps=result.velocity_mps.tolist(),
        acceleration_mps2=result.acceleration_mps2.tolist(),
        f_traction_n=result.f_traction_n.tolist(),
        wheel_torque_nm=result.wheel_torque_nm.tolist(),
        wheel_power_w=result.wheel_power_w.tolist(),
        summary=result.summary(),
    )


# ---------- Phase 3: ICE ----------

class ICEPowertrainParams(BaseModel):
    max_torque_nm: float = Field(..., gt=0)
    max_power_w: float = Field(..., gt=0)
    gear_ratio: float = Field(..., gt=0)
    final_drive_ratio: float = Field(..., gt=0)
    transmission_efficiency: float = Field(0.92, gt=0, le=1)
    engine_efficiency: float = Field(0.30, gt=0, le=1)
    fuel_type: str = Field("gasoline", pattern="^(gasoline|diesel)$")
    max_rpm: float = 7000.0


class RunICESimulationRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    powertrain: ICEPowertrainParams
    drive_cycle_name: str = "simple_test_cycle"


class RunICESimulationResponse(BaseModel):
    time_s: list[float]
    velocity_mps: list[float]
    wheel_torque_nm: list[float]
    wheel_power_w: list[float]
    engine_torque_nm: list[float]
    engine_rpm: list[float]
    engine_power_w: list[float]
    fuel_power_w: list[float]
    summary: dict


def _build_ice_powertrain(p: ICEPowertrainParams) -> ICEPowertrain:
    return ICEPowertrain(
        max_torque_nm=p.max_torque_nm,
        max_power_w=p.max_power_w,
        gear_ratio=p.gear_ratio,
        final_drive_ratio=p.final_drive_ratio,
        transmission_efficiency=p.transmission_efficiency,
        engine_efficiency=p.engine_efficiency,
        fuel_lhv_j_per_l=FUEL_LHV_BY_TYPE[p.fuel_type],
        max_rpm=p.max_rpm,
    )


@router.post("/run-ice", response_model=RunICESimulationResponse)
def run_ice_simulation(payload: RunICESimulationRequest) -> RunICESimulationResponse:
    vehicle = _build_vehicle(payload.vehicle)
    environment = _build_environment(payload.environment)
    drive_cycle = _get_drive_cycle(payload.drive_cycle_name)
    powertrain = _build_ice_powertrain(payload.powertrain)

    simulation = ICEVehicleSimulation(
        vehicle=vehicle, environment=environment, drive_cycle=drive_cycle, powertrain=powertrain
    )
    result = simulation.run()

    return RunICESimulationResponse(
        time_s=result.time_s.tolist(),
        velocity_mps=result.velocity_mps.tolist(),
        wheel_torque_nm=result.wheel_torque_nm.tolist(),
        wheel_power_w=result.wheel_power_w.tolist(),
        engine_torque_nm=result.engine_torque_nm.tolist(),
        engine_rpm=result.engine_rpm.tolist(),
        engine_power_w=result.engine_power_w.tolist(),
        fuel_power_w=result.fuel_power_w.tolist(),
        summary=result.summary(),
    )


# ---------- Phase 4: BEV ----------

class MotorParams(BaseModel):
    max_torque_nm: float = Field(..., gt=0)
    max_power_w: float = Field(..., gt=0)
    gear_ratio: float = Field(..., gt=0)
    final_drive_ratio: float = Field(..., gt=0)
    transmission_efficiency: float = Field(0.95, gt=0, le=1)
    motor_efficiency: float = Field(0.92, gt=0, le=1)
    inverter_efficiency: float = Field(0.97, gt=0, le=1)
    regen_efficiency: float = Field(0.7, gt=0, le=1)


class BatteryParams(BaseModel):
    capacity_wh: float = Field(..., gt=0)
    initial_soc: float = Field(0.7, ge=0, le=1)
    min_soc: float = Field(0.1, ge=0, le=1)
    max_soc: float = Field(1.0, ge=0, le=1)
    internal_efficiency: float = Field(0.95, gt=0, le=1)


class RunBEVSimulationRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    motor: MotorParams
    battery: BatteryParams
    drive_cycle_name: str = "simple_test_cycle"


class RunBEVSimulationResponse(BaseModel):
    time_s: list[float]
    velocity_mps: list[float]
    motor_torque_nm: list[float]
    motor_rpm: list[float]
    motor_power_w: list[float]
    battery_power_w: list[float]
    soc: list[float]
    summary: dict


def _build_motor(p: MotorParams) -> Motor:
    return Motor(
        max_torque_nm=p.max_torque_nm,
        max_power_w=p.max_power_w,
        gear_ratio=p.gear_ratio,
        final_drive_ratio=p.final_drive_ratio,
        transmission_efficiency=p.transmission_efficiency,
        motor_efficiency=p.motor_efficiency,
        inverter_efficiency=p.inverter_efficiency,
        regen_efficiency=p.regen_efficiency,
    )


def _build_battery(p: BatteryParams) -> Battery:
    return Battery(
        capacity_wh=p.capacity_wh,
        initial_soc=p.initial_soc,
        min_soc=p.min_soc,
        max_soc=p.max_soc,
        internal_efficiency=p.internal_efficiency,
    )


@router.post("/run-bev", response_model=RunBEVSimulationResponse)
def run_bev_simulation(payload: RunBEVSimulationRequest) -> RunBEVSimulationResponse:
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

    return RunBEVSimulationResponse(
        time_s=result.time_s.tolist(),
        velocity_mps=result.velocity_mps.tolist(),
        motor_torque_nm=result.motor_torque_nm.tolist(),
        motor_rpm=result.motor_rpm.tolist(),
        motor_power_w=result.motor_power_w.tolist(),
        battery_power_w=result.battery_power_w.tolist(),
        soc=result.soc.tolist(),
        summary=result.summary(),
    )


# ---------- Phase 4: Hybrid ----------

class RunHybridSimulationRequest(BaseModel):
    vehicle: VehicleParams
    environment: EnvironmentParams = EnvironmentParams()
    ice: ICEPowertrainParams
    motor: MotorParams
    battery: BatteryParams
    electric_only_power_threshold_w: float = 15_000.0
    motor_assist_fraction: float = Field(0.3, ge=0, le=1)
    drive_cycle_name: str = "simple_test_cycle"


class RunHybridSimulationResponse(BaseModel):
    time_s: list[float]
    velocity_mps: list[float]
    ice_torque_nm: list[float]
    ice_rpm: list[float]
    ice_power_w: list[float]
    fuel_power_w: list[float]
    motor_torque_nm: list[float]
    motor_rpm: list[float]
    motor_power_w: list[float]
    battery_power_w: list[float]
    soc: list[float]
    summary: dict


@router.post("/run-hybrid", response_model=RunHybridSimulationResponse)
def run_hybrid_simulation(payload: RunHybridSimulationRequest) -> RunHybridSimulationResponse:
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

    return RunHybridSimulationResponse(
        time_s=result.time_s.tolist(),
        velocity_mps=result.velocity_mps.tolist(),
        ice_torque_nm=result.ice_torque_nm.tolist(),
        ice_rpm=result.ice_rpm.tolist(),
        ice_power_w=result.ice_power_w.tolist(),
        fuel_power_w=result.fuel_power_w.tolist(),
        motor_torque_nm=result.motor_torque_nm.tolist(),
        motor_rpm=result.motor_rpm.tolist(),
        motor_power_w=result.motor_power_w.tolist(),
        battery_power_w=result.battery_power_w.tolist(),
        soc=result.soc.tolist(),
        summary=result.summary(),
    )