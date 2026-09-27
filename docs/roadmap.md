# Roadmap

## Concept

**Vehicle Physics Digital Twin Platform** — a web-based platform for
modelling, simulating and comparing the physical behaviour and energy
performance of internal-combustion, hybrid and battery-electric
vehicles under common driving conditions, built on one shared
vehicle-dynamics framework rather than three independent simulators.

## Versioning Overview

VERSION 1 — Physics-based Vehicle Simulator (Phases 1-4)
|
VERSION 2 — Vehicle Engineering Analysis Platform (Phases 5-6)
|
VERSION 3 — Vehicle Digital Twin Platform (Phases 7-8)


## Phase Breakdown

### Phase 1 — Physical Framework ✅
Core longitudinal dynamics equations (rolling, aero, grade,
acceleration forces), the `Vehicle` parameter model, and drive cycle
representation. Exposed via `POST /api/vehicles/check-physics`.

**Output**: a standalone physics library + single-point check page
(`vehicle.html`).

### Phase 2 — Vehicle Dynamics Engine ✅
Time-domain simulation engine (`VehicleDynamicsSimulation`) that runs
a full drive cycle through the longitudinal dynamics model, no
powertrain yet. Exposed via `POST /api/simulation/run`.

**Output**: full time-series simulation (`simulation.html`), plottable
via Chart.js.

### Phase 3 — ICE Powertrain ✅
Engine + transmission model (`ICEPowertrain`), converting wheel
torque demand into engine torque/RPM/power and fuel consumption.
Exposed via `POST /api/simulation/run-ice`.

**Output**: engine RPM/torque/power and fuel-consumption charts.

### Phase 4 — Hybrid + BEV Powertrain ✅
`Motor` and `Battery` models shared by BEV and Hybrid; `BEVPowertrain`
(motor + battery) and `HybridPowertrain` (ICE + motor + battery with
a rule-based controller). Exposed via `POST /api/simulation/run-bev`
and `POST /api/simulation/run-hybrid`.

**Output**: SOC, battery power, and motor charts for both powertrains.

### Phase 5 — Energy, Thermal & Analysis ✅
Energy flow breakdown per powertrain (fuel/battery -> mechanical ->
wheel, with stage efficiencies) and a lumped thermal model applied to
the battery. Exposed via `POST /api/analysis/energy-{ice,bev,hybrid}`.

**Output**: `analysis.html` — energy breakdown tables and bar charts.

### Phase 6 — Web Platform & Visualization ✅
Shared navbar (`nav.js`) injected into every page so navigation
doesn't require returning to the homepage; visual refresh of
`style.css` using CSS variables, card-based sections, and responsive
grid layout for input forms.

**Output**: consistent, navigable UI across all pages.

### Phase 7 — Real-World Data & Validation ✅
CSV upload and parsing (`real_data.py`), model-vs-real comparison
using MAE/RMSE/max-error/bias (`validation.py`). Since the model is
open-loop (it follows the drive cycle's measured speed exactly),
validation compares *derived* quantities (SOC for BEV, cumulative
fuel for ICE) rather than speed itself. Exposed via
`POST /api/validation/upload`, `/validate-bev`, `/validate-ice`.

**Output**: `validation.html` — CSV upload, preview, and model-vs-real
comparison charts.

### Phase 8 — Digital Twin & Comparative Analysis ✅
Runs ICE, Hybrid and BEV simulations under identical vehicle body,
environment and drive cycle, producing a unified comparison table and
overlay charts. This is the platform's core "controlled experiment"
capability. Exposed via `POST /api/comparison/run`.

**Output**: `comparison.html` — 3-column metric table and overlay
charts (torque, battery power, SOC) across all three powertrains.

## Phase-to-Version Mapping

| Version | Phases | Focus |
|---|---|---|
| V1 — Physics Simulator | 1-4 | Physical model + vehicle dynamics + ICE/Hybrid/BEV powertrains |
| V2 — Engineering Analysis | 5-6 | Energy/thermal analysis + polished web platform |
| V3 — Digital Twin | 7-8 | Real data validation + full digital twin + comparative analysis |

## Design Principle Carried Through Every Phase

ICE, Hybrid and BEV are never three separate projects — they are
three powertrain implementations plugged into one shared
`Vehicle` + `Environment` + `DriveCycle` framework:
              DRIVE CYCLE
                   |
                   v
          +----------------+
          | Vehicle        |
          | Dynamics       |
          +--------+-------+
                   |
             Wheel Demand
                   |
    +--------------+--------------+
    v              v              v
   ICE          HYBRID           BEV
    |              |              |
    +--------------+--------------+
                   v
           Energy Analysis
                   |
                   v
            Thermal / SOC
                   |
                   v
              RESULTS
                   |
                   v
             REAL DATA
                   |
                   v
             DIGITAL TWIN

## Known V1-V3 Simplifications (candidates for a future V4)

- Single fixed gear ratio, no gear shifting logic
- Constant engine/motor efficiency (no torque-RPM efficiency map)
- Open-loop vehicle dynamics (no driver/controller model — the
  vehicle exactly follows the drive cycle's target speed)
- Rule-based hybrid energy management (not optimal/predictive control)
- Thermal model implemented for the battery only; motor and engine
  thermal tracking can be added using the same `ThermalParams` /
  `ThermalState` pattern already in place
- Only one built-in synthetic drive cycle (`simple_test_cycle`);
  standard cycles (WLTP, UDDS, FTP-75) would need to be added as CSV
  data under `data/drive_cycles/`
- No persistent database; results are computed on demand and not
  stored between sessions (SQLite tables were planned in the original
  structure under `backend/app/models/` but not yet wired into the API)