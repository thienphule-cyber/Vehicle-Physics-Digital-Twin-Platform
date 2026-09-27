# API Reference

Base URL (local development): `http://localhost:{BACKEND_PORT}`
(port is auto-assigned by `start.sh` and written to `frontend/js/config.js`)

All endpoints accept and return JSON. Request bodies are validated
with Pydantic; invalid input returns HTTP 422 with a `detail` field
describing the validation error.

## Health

### `GET /api/health`
Simple health check.

**Response**
```json
{ "status": "ok" }
```

---

## Vehicle (Phase 1)

### `POST /api/vehicles/check-physics`
Single-point physics check: given vehicle/environment parameters and
one instantaneous state (velocity, acceleration), returns the force
breakdown, wheel torque and wheel power.

**Request**
```json
{
  "mass": 1600,
  "wheel_radius": 0.34,
  "drag_coefficient": 0.29,
  "frontal_area": 2.2,
  "rolling_resistance_coefficient": 0.012,
  "air_density": 1.225,
  "road_grade_deg": 0,
  "wind_speed": 0,
  "velocity": 20,
  "acceleration": 0
}
```

**Response**
```json
{
  "f_rolling": 188.35,
  "f_aero": 165.05,
  "f_grade": 0.0,
  "f_acc": 0.0,
  "f_traction": 353.4,
  "wheel_torque_nm": 120.16,
  "wheel_power_kw": 7.07
}
```

---

## Simulation (Phase 2, 3, 4)

### `GET /api/simulation/drive-cycles`
Returns the list of available drive cycle names.

**Response**
```json
["simple_test_cycle"]
```

### `POST /api/simulation/run`
Pure vehicle dynamics simulation over a drive cycle (no powertrain).

**Request**
```json
{
  "vehicle": { "mass": 1600, "wheel_radius": 0.34, "drag_coefficient": 0.29,
               "frontal_area": 2.2, "rolling_resistance_coefficient": 0.012 },
  "environment": { "air_density": 1.225, "road_grade_deg": 0, "wind_speed": 0 },
  "drive_cycle_name": "simple_test_cycle"
}
```

**Response**: time-series (`time_s`, `velocity_mps`, `acceleration_mps2`,
`f_traction_n`, `wheel_torque_nm`, `wheel_power_w`) plus `summary`.

### `POST /api/simulation/run-ice`
Vehicle dynamics + ICE powertrain simulation.

**Additional request field** `powertrain`:
```json
{
  "max_torque_nm": 250,
  "max_power_w": 110000,
  "gear_ratio": 3.5,
  "final_drive_ratio": 3.9,
  "transmission_efficiency": 0.92,
  "engine_efficiency": 0.30,
  "fuel_type": "gasoline",
  "max_rpm": 7000
}
```

**Response**: time-series (`engine_torque_nm`, `engine_rpm`,
`engine_power_w`, `fuel_power_w`, ...) plus `summary` including
`total_fuel_volume_l` and `avg_fuel_consumption_l_per_100km`.

### `POST /api/simulation/run-bev`
Vehicle dynamics + BEV (motor + battery) powertrain simulation.

**Additional request fields** `motor` and `battery`:
```json
{
  "motor": { "max_torque_nm": 300, "max_power_w": 150000,
             "gear_ratio": 9.0, "final_drive_ratio": 1.0 },
  "battery": { "capacity_wh": 60000, "initial_soc": 0.7,
               "min_soc": 0.1, "max_soc": 1.0 }
}
```

**Response**: time-series (`motor_torque_nm`, `motor_rpm`,
`motor_power_w`, `battery_power_w`, `soc`) plus `summary` including
`final_soc_pct`, `total_energy_kwh`, `regen_energy_kwh`.

### `POST /api/simulation/run-hybrid`
Vehicle dynamics + Hybrid (ICE + motor + battery) powertrain simulation.

**Additional request fields**: `ice`, `motor`, `battery`,
`electric_only_power_threshold_w` (default 15000),
`motor_assist_fraction` (default 0.3).

**Response**: time-series for both ICE and motor branches
(`ice_torque_nm`, `motor_torque_nm`, `battery_power_w`, `soc`, ...)
plus `summary`.

---

## Analysis (Phase 5)

### `POST /api/analysis/energy-ice`
Same request shape as `/run-ice`. Returns an energy breakdown instead
of raw time-series.

**Response**
```json
{
  "fuel_energy_kwh": 1.42,
  "engine_mechanical_energy_kwh": 0.43,
  "wheel_energy_kwh": 0.35,
  "engine_efficiency_pct": 30.3,
  "transmission_efficiency_pct": 81.4,
  "overall_efficiency_pct": 24.6
}
```

### `POST /api/analysis/energy-bev`
Same request shape as `/run-bev`.

**Response**
```json
{
  "battery_discharge_energy_kwh": 0.51,
  "regen_energy_kwh": 0.08,
  "motor_mechanical_energy_kwh": 0.44,
  "wheel_energy_kwh": 0.35,
  "motor_efficiency_pct": 86.3,
  "overall_efficiency_pct": 68.6
}
```

### `POST /api/analysis/energy-hybrid`
Same request shape as `/run-hybrid`.

**Response**
```json
{
  "fuel_energy_kwh": 0.61,
  "battery_discharge_energy_kwh": 0.12,
  "regen_energy_kwh": 0.05,
  "ice_mechanical_energy_kwh": 0.18,
  "motor_mechanical_energy_kwh": 0.10,
  "wheel_energy_kwh": 0.35,
  "overall_efficiency_pct": 47.9
}
```

---

## Validation (Phase 7)

### `POST /api/validation/upload`
Parses uploaded CSV text and returns a preview.

**Request**
```json
{ "csv_text": "time_s,speed_kmh,soc\n0,0,0.80\n...", "source_name": "test_drive.csv" }
```

**Response**
```json
{
  "source_name": "test_drive.csv",
  "num_points": 31,
  "duration_s": 30.0,
  "max_speed_kmh": 60.0,
  "available_reference_columns": ["soc"],
  "preview_time_s": [0, 5, 10, ...],
  "preview_speed_kmh": [0, 20, 40, ...]
}
```

### `POST /api/validation/validate-bev`
Runs a BEV simulation using the uploaded data's speed profile as the
drive cycle, then compares model SOC against the real `soc` column
(required in the CSV).

**Request**: `vehicle`, `environment`, `motor`, `battery`, `csv_text`, `source_name`.

**Response**
```json
{
  "quantity": "soc",
  "comparison": {
    "time_s": [...], "model_values": [...], "real_values": [...], "error": [...],
    "mae": 0.0021, "rmse": 0.0034, "max_error": 0.008, "bias": -0.0005
  },
  "model_summary": { ... }
}
```

### `POST /api/validation/validate-ice`
Same pattern, comparing model cumulative fuel volume against the real
`fuel_l` column (required in the CSV).

**Request**: `vehicle`, `environment`, `powertrain`, `csv_text`, `source_name`.

**Response**: same shape as `/validate-bev`, with `"quantity": "cumulative_fuel_l"`.

**Required CSV columns**: `time_s`, `speed_kmh` (always); `soc`
(for BEV validation) or `fuel_l` (for ICE validation, cumulative
liters consumed).

---

## Comparison (Phase 8)

### `POST /api/comparison/run`
Runs ICE, Hybrid and BEV simulations under identical vehicle body,
environment and drive cycle, and returns a unified comparison.

**Request**
```json
{
  "vehicle": { ... },
  "environment": { ... },
  "drive_cycle_name": "simple_test_cycle",
  "ice": { ... },
  "motor": { ... },
  "bev_battery": { "capacity_wh": 60000, "initial_soc": 0.7, ... },
  "hybrid_battery": { "capacity_wh": 1500, "initial_soc": 0.6, ... },
  "electric_only_power_threshold_w": 15000,
  "motor_assist_fraction": 0.3
}
```

**Response**
```json
{
  "time_s": [...],
  "ice_result": { "engine_torque_nm": [...], "summary": {...}, "energy_breakdown": {...} },
  "hybrid_result": { "ice_torque_nm": [...], "motor_torque_nm": [...], "soc": [...], "summary": {...}, "energy_breakdown": {...} },
  "bev_result": { "motor_torque_nm": [...], "soc": [...], "summary": {...}, "energy_breakdown": {...} },
  "comparison_table": {
    "distance_km": { "ice": 0.28, "hybrid": 0.28, "bev": 0.28 },
    "max_speed_kmh": { "ice": 60.0, "hybrid": 60.0, "bev": 60.0 },
    "overall_efficiency_pct": { "ice": 24.6, "hybrid": 47.9, "bev": 68.6 },
    "fuel_used_l": { "ice": 0.043, "hybrid": 0.018, "bev": 0.0 },
    "energy_used_kwh": { "ice": 0.0, "hybrid": 0.12, "bev": 0.51 },
    "regen_energy_kwh": { "ice": 0.0, "hybrid": 0.05, "bev": 0.08 },
    "final_soc_pct": { "ice": null, "hybrid": 59.2, "bev": 79.1 }
  }
}
```

---

## Error Responses

All endpoints return errors in FastAPI's standard shape:

```json
{ "detail": "Unknown drive cycle: xyz" }
```

or, for validation errors:

```json
{ "detail": [ { "loc": ["body", "vehicle", "mass"], "msg": "...", "type": "..." } ] }
```

HTTP status codes used: `200` (success), `400` (bad request, e.g.
missing CSV column), `404` (unknown drive cycle), `422` (Pydantic
validation error).