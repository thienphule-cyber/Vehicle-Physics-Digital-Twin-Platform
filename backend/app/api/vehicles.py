"""
Vehicle-related API endpoints.

Phase 1 exposes a single endpoint that runs the longitudinal dynamics
physics core for one instantaneous vehicle state. This lets the
frontend verify the physics equations against real backend
computation, before the full simulation engine (Phase 2) exists.
"""

import math

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.vehicle import Vehicle
from app.physics.longitudinal import (
    Environment,
    traction_force,
    rolling_resistance_force,
    aerodynamic_drag_force,
    grade_force,
    acceleration_force,
    wheel_torque,
    wheel_power,
)

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


class PhysicsCheckRequest(BaseModel):
    """Input payload for a single-point physics check."""

    mass: float = Field(..., gt=0)
    wheel_radius: float = Field(..., gt=0)
    drag_coefficient: float = Field(..., ge=0)
    frontal_area: float = Field(..., gt=0)
    rolling_resistance_coefficient: float = Field(..., ge=0)

    air_density: float = 1.225
    road_grade_deg: float = 0.0
    wind_speed: float = 0.0

    velocity: float
    acceleration: float = 0.0


class PhysicsCheckResponse(BaseModel):
    """Output payload with the force/torque/power breakdown."""

    f_rolling: float
    f_aero: float
    f_grade: float
    f_acc: float
    f_traction: float
    wheel_torque_nm: float
    wheel_power_kw: float


@router.post("/check-physics", response_model=PhysicsCheckResponse)
def check_physics(payload: PhysicsCheckRequest) -> PhysicsCheckResponse:
    """
    Compute traction force, wheel torque and wheel power for a single
    vehicle state (velocity + acceleration), given vehicle and
    environment parameters.
    """
    vehicle = Vehicle(
        mass=payload.mass,
        wheel_radius=payload.wheel_radius,
        drag_coefficient=payload.drag_coefficient,
        frontal_area=payload.frontal_area,
        rolling_resistance_coefficient=payload.rolling_resistance_coefficient,
    )

    environment = Environment(
        air_density=payload.air_density,
        road_grade_rad=math.radians(payload.road_grade_deg),
        wind_speed=payload.wind_speed,
    )

    f_rolling = (
        rolling_resistance_force(vehicle) if payload.velocity != 0 else 0.0
    )
    f_aero = aerodynamic_drag_force(vehicle, environment, payload.velocity)
    f_grade = grade_force(vehicle, environment)
    f_acc = acceleration_force(vehicle, payload.acceleration)

    f_traction = traction_force(
        vehicle, environment, payload.velocity, payload.acceleration
    )

    torque = wheel_torque(f_traction, vehicle)
    power_kw = wheel_power(f_traction, payload.velocity) / 1000

    return PhysicsCheckResponse(
        f_rolling=f_rolling,
        f_aero=f_aero,
        f_grade=f_grade,
        f_acc=f_acc,
        f_traction=f_traction,
        wheel_torque_nm=torque,
        wheel_power_kw=power_kw,
    )