# Physics Model

## Purpose

This document describes the physical equations implemented in the
platform, shared across ICE, Hybrid and BEV powertrains.

## 1. Longitudinal Vehicle Dynamics (shared by all powertrains)

The traction force required at the wheel is the sum of four
components:

F_traction = F_rolling + F_aero + F_grade + F_acc


### Rolling resistance

F_rolling = C_rr * m * g

Applied only when the vehicle is moving (v != 0).

### Aerodynamic drag

F_aero = 0.5 * rho * C_d * A * v_rel^2

where `v_rel = v + wind_speed` (headwind convention), and the sign of
the force follows the sign of `v_rel` so drag always opposes motion.

### Road grade

F_grade = m * g * sin(theta)

`theta` is the road grade angle in radians (positive = uphill).

### Acceleration (inertial force)

F_acc = m * a


### Wheel torque and power

T_wheel = F_traction * r_wheel
P_wheel = F_traction * v


Implemented in `backend/app/physics/longitudinal.py`.

## 2. Drivetrain (wheel <-> engine/motor conversion)

Shared conversion equations between wheel-side and engine/motor-side
quantities, used by ICE, Hybrid and BEV:

omega_wheel = v / r_wheel
omega_engine = omega_wheel * gear_ratio * final_drive_ratio

T_engine = T_wheel / (gear_ratio * final_drive_ratio * eta_transmission)


Implemented in `backend/app/physics/drivetrain.py`.

## 3. ICE Powertrain

Fuel -> Combustion -> Engine -> Transmission -> Wheel


Engine torque/power are derived from wheel torque demand through the
drivetrain equations above, then saturated at `max_torque_nm` and
`max_power_w`.

P_engine = T_engine * omega_engine
P_fuel = P_engine / eta_engine (only when P_engine > 0)


Fuel energy is converted to volume using the fuel's lower heating
value (LHV):

V_fuel = E_fuel / LHV


Gasoline LHV ~ 34.2 MJ/L, Diesel LHV ~ 38.6 MJ/L (approximate,
constant values for V1).

Implemented in `backend/app/models/ice.py`,
`backend/app/physics/energy.py`.

## 4. Electric Motor

Used by both BEV and Hybrid powertrains. Positive wheel torque = driving
(motor provides torque, battery discharges). Negative wheel torque =
braking (motor absorbs torque, battery charges via regeneration).

P_motor = T_motor * omega_motor

Driving (P_motor >= 0):
P_battery = P_motor / (eta_motor * eta_inverter)

Regenerative braking (P_motor < 0):
P_battery = P_motor * eta_motor * eta_inverter * eta_regen


`eta_regen` captures the fact that not all braking torque can be
recovered electrically (some is lost to friction braking, tire slip
limits, etc).

Implemented in `backend/app/models/motor.py`.

## 5. Battery

State of charge is integrated forward in time:

SOC[k+1] = SOC[k] - (P_battery * dt) / E_battery


Positive `P_battery` (discharging) draws `P_battery / eta_internal`
from the battery; negative `P_battery` (charging) stores
`|P_battery| * eta_internal`. SOC is clamped to `[min_soc, max_soc]`.

Implemented in `backend/app/models/battery.py`.

## 6. BEV Powertrain

Battery -> Inverter -> Motor -> Gear -> Wheel


Simplest powertrain: a single `Motor` drawing from a single `Battery`,
stepped together each timestep.

Implemented in `backend/app/models/bev.py`,
`backend/app/simulation/bev_simulation.py`.

## 7. Hybrid Powertrain
         ICE Engine
             |
             v
        Transmission
             |
             v
           Wheels
             ^
             |
        Electric Motor
             |
          Inverter
             |
          Battery

V1 uses a simple rule-based energy management controller:

- **Braking** (wheel power demand < 0): motor handles regeneration
  only, ICE contributes nothing.
- **Low demand** (0 <= wheel power <= `electric_only_power_threshold_w`):
  electric-only drive.
- **High demand** (wheel power > threshold): torque is split between
  motor (`motor_assist_fraction`) and ICE (the remainder).

This is a deliberate V1 simplification; SOC-aware or optimal control
strategies are a later-phase improvement.

Implemented in `backend/app/models/hybrid.py`,
`backend/app/simulation/hybrid_simulation.py`.

## 8. Thermal Model (lumped parameter)

A single thermal mass exchanging heat with ambient through convective
cooling:

C_th * dT/dt = P_loss - hA(T - T_amb)


Integrated with forward Euler per timestep:

dT = (P_loss - hA(T - T_amb)) / C_th * dt


Currently applied to the battery (heat generated proportional to
`|battery_power| * heat_loss_fraction`, where
`heat_loss_fraction = 1 - eta_internal` by default). Motor and engine
thermal models can be added using the same `ThermalParams` /
`ThermalState` pattern.

Implemented in `backend/app/physics/thermal.py`.

## 9. Energy Flow Analysis

For each powertrain, cumulative energies are computed by integrating
power time-series (trapezoidal rule) and expressed as stage
efficiencies:

- **ICE**: Fuel energy -> Engine mechanical energy -> Wheel energy
- **BEV**: Battery discharge energy (+ regen) -> Motor mechanical
  energy -> Wheel energy
- **Hybrid**: combines both fuel and battery energy sources into one
  wheel-energy result

Implemented in `backend/app/analysis/metrics.py`.

## 10. Validation Metrics

Model output is compared against real (measured) data using standard
error metrics, after interpolating the real data onto the model's
time grid:

MAE = mean(|model - real|)
RMSE = sqrt(mean((model - real)^2))
Max error = max(|model - real|)
Bias = mean(model - real)


Because the model is currently open-loop (it follows the drive
cycle's speed profile exactly), validation compares *derived*
quantities — SOC for BEV, cumulative fuel volume for ICE — rather
than speed itself.

Implemented in `backend/app/analysis/validation.py`.

## Known V1 Simplifications

- Single fixed gear ratio (no gear shifting logic)
- Constant engine/motor efficiency (no torque-RPM efficiency map)
- Open-loop vehicle dynamics (vehicle exactly follows the drive
  cycle's target speed; no driver/controller model)
- Rule-based hybrid control (not optimal control)
- Thermal model implemented for battery only (V1); motor/engine
  thermal follow the same pattern in a later iteration