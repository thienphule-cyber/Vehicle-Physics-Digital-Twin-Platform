# Vehicle Physics Digital Twin Platform

A web-based platform for modelling, simulating and comparing the
physical behaviour and energy performance of internal-combustion
(ICE), hybrid, and battery-electric (BEV) vehicles under a shared
vehicle-dynamics framework — rather than as three independent
simulators.

Built as a mechanical/mechatronics engineering portfolio project
combining vehicle dynamics, thermodynamics, electrical systems,
control, numerical simulation, and web development.

## What it does

- Simulates ICE, Hybrid, and BEV vehicles over a driving cycle, using
  one shared physics core for vehicle dynamics.
- Computes energy flow breakdown (fuel/battery → mechanical → wheel)
  and stage efficiencies for each powertrain.
- Validates model predictions (SOC, fuel consumption) against
  uploaded real-world vehicle data (CSV), using MAE/RMSE/max-error
  metrics.
- Runs all three powertrains under identical vehicle body,
  environment, and driving cycle for a controlled, side-by-side
  comparison.

## Tech stack

- **Backend**: Python, FastAPI, NumPy, SciPy, Pandas
- **Frontend**: plain HTML/CSS/JavaScript, Chart.js (no framework)
- **Testing**: pytest

## Project structure

backend/ FastAPI app: physics, powertrain models, simulation engines, analysis
frontend/ Static HTML/CSS/JS pages, one per feature area
data/ Drive cycles and real vehicle data (CSV)
docs/ Architecture, physics model, API reference, roadmap
start.sh Launches backend + frontend for local testing
stop.sh Stops both servers


See `docs/architecture.md` for the full breakdown, `docs/physics_model.md`
for the equations implemented, `docs/api_reference.md` for every
endpoint, and `docs/roadmap.md` for how the project was built phase by
phase (V1 → V3).

## Getting started

### Prerequisites
- Python 3.10+
- `pip`

### Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --break-system-packages
```

### Run
```bash
chmod +x start.sh stop.sh
./start.sh
```
This starts the backend and frontend as background processes, picks
free ports automatically, and opens the homepage in your browser. No
need to keep a terminal open.

To stop:
```bash
./stop.sh
```

Logs are written to `.run/logs/backend.log` and `.run/logs/frontend.log`.

### Run tests
```bash
cd backend
source venv/bin/activate
pytest -v
```

## Pages

| Page | Description |
|---|---|
| `vehicle.html` | Single-point physics check (forces, torque, power) |
| `simulation.html` | Full drive-cycle simulation for ICE / BEV / Hybrid |
| `analysis.html` | Energy flow breakdown and stage efficiency |
| `validation.html` | Upload real vehicle data, compare model vs real |
| `comparison.html` | Side-by-side ICE vs Hybrid vs BEV under identical conditions |

## Development roadmap

The project was built incrementally across 8 phases, each producing a
runnable result:

Phase 1 Physical Framework
Phase 2 Vehicle Dynamics Engine
Phase 3 ICE Powertrain
Phase 4 Hybrid + BEV Powertrain
Phase 5 Energy, Thermal & Analysis
Phase 6 Web Platform & Visualization
Phase 7 Real-World Data & Validation
Phase 8 Digital Twin & Comparative Analysis


Full details in `docs/roadmap.md`.

## Known limitations (V1)

- Single fixed gear ratio (no gear shifting)
- Constant engine/motor efficiency (no torque-RPM efficiency map)
- Open-loop vehicle dynamics (no driver/controller model)
- Rule-based hybrid control (not optimal control)
- Thermal model currently applied to the battery only

See `docs/physics_model.md` and `docs/roadmap.md` for the full list
and how these could be extended.

## License

This is a personal portfolio project. No license specified yet.