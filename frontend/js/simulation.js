/**
 * Page logic for simulation.html (Phase 2 + 3 + 4).
 */

let charts = {};

// ---------- Shared input readers ----------

function readVehicleParams() {
  return {
    mass: parseFloat(document.getElementById("mass").value),
    wheel_radius: parseFloat(document.getElementById("wheelRadius").value),
    drag_coefficient: parseFloat(document.getElementById("dragCoefficient").value),
    frontal_area: parseFloat(document.getElementById("frontalArea").value),
    rolling_resistance_coefficient: parseFloat(
      document.getElementById("rollingCoefficient").value
    ),
  };
}

function readEnvironmentParams() {
  return {
    air_density: parseFloat(document.getElementById("airDensity").value),
    road_grade_deg: parseFloat(document.getElementById("roadGradeDeg").value),
    wind_speed: parseFloat(document.getElementById("windSpeed").value),
  };
}

function readDriveCycleName() {
  return document.getElementById("driveCycleSelect").value;
}

function readIcePowertrainParams() {
  return {
    max_torque_nm: parseFloat(document.getElementById("iceMaxTorque").value),
    max_power_w: parseFloat(document.getElementById("iceMaxPower").value) * 1000,
    gear_ratio: parseFloat(document.getElementById("iceGearRatio").value),
    final_drive_ratio: parseFloat(document.getElementById("iceFinalDrive").value),
    transmission_efficiency: parseFloat(document.getElementById("iceTransEff").value),
    engine_efficiency: parseFloat(document.getElementById("iceEngineEff").value),
    fuel_type: document.getElementById("iceFuelType").value,
  };
}

function readMotorParams() {
  return {
    max_torque_nm: parseFloat(document.getElementById("motorMaxTorque").value),
    max_power_w: parseFloat(document.getElementById("motorMaxPower").value) * 1000,
    gear_ratio: parseFloat(document.getElementById("motorGearRatio").value),
    final_drive_ratio: parseFloat(document.getElementById("motorFinalDrive").value),
    transmission_efficiency: parseFloat(document.getElementById("motorTransEff").value),
    motor_efficiency: parseFloat(document.getElementById("motorEff").value),
    inverter_efficiency: parseFloat(document.getElementById("inverterEff").value),
    regen_efficiency: parseFloat(document.getElementById("regenEff").value),
  };
}

function readBevBatteryParams() {
  return {
    capacity_wh: parseFloat(document.getElementById("batteryCapacityBev").value) * 1000,
    initial_soc: parseFloat(document.getElementById("batteryInitialSoc").value),
    min_soc: parseFloat(document.getElementById("batteryMinSoc").value),
    max_soc: parseFloat(document.getElementById("batteryMaxSoc").value),
    internal_efficiency: parseFloat(document.getElementById("batteryInternalEff").value),
  };
}

function readHybridBatteryParams() {
  return {
    capacity_wh: parseFloat(document.getElementById("hybridBatteryCapacity").value) * 1000,
    initial_soc: parseFloat(document.getElementById("batteryInitialSoc").value),
    min_soc: parseFloat(document.getElementById("batteryMinSoc").value),
    max_soc: parseFloat(document.getElementById("batteryMaxSoc").value),
    internal_efficiency: parseFloat(document.getElementById("batteryInternalEff").value),
  };
}

// ---------- Chart helper ----------

function renderLineChart(canvasId, label, timeS, values, color) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  if (charts[canvasId]) {
    charts[canvasId].destroy();
  }

  charts[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels: timeS.map((t) => t.toFixed(0)),
      datasets: [
        {
          label: label,
          data: values,
          borderColor: color,
          backgroundColor: color,
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: { title: { display: true, text: "Time (s)" } },
        y: { title: { display: true, text: label } },
      },
      plugins: {
        legend: { display: false },
        title: { display: true, text: label },
      },
    },
  });
}

// ---------- Phase 2: vehicle dynamics ----------

function renderSummary(summary) {
  document.getElementById("sumDuration").textContent = summary.duration_s.toFixed(1);
  document.getElementById("sumDistance").textContent = summary.distance_km.toFixed(3);
  document.getElementById("sumMaxSpeed").textContent = summary.max_speed_kmh.toFixed(1);
  document.getElementById("sumMaxForce").textContent =
    summary.max_traction_force_n.toFixed(1);
  document.getElementById("sumMaxPower").textContent =
    summary.max_wheel_power_kw.toFixed(2);
  document.getElementById("sumMaxTorque").textContent =
    summary.peak_wheel_torque_nm.toFixed(1);
}

function renderDynamicsCharts(result) {
  const speedKmh = result.velocity_mps.map((v) => v * 3.6);
  renderLineChart("speedChart", "Speed (km/h)", result.time_s, speedKmh, "#2b6cb0");
  renderLineChart(
    "accelerationChart", "Acceleration (m/s^2)", result.time_s,
    result.acceleration_mps2, "#c0392b"
  );
  renderLineChart(
    "forceChart", "Traction force (N)", result.time_s, result.f_traction_n, "#27ae60"
  );
  renderLineChart(
    "torqueChart", "Wheel torque (N·m)", result.time_s, result.wheel_torque_nm, "#8e44ad"
  );
  const powerKw = result.wheel_power_w.map((p) => p / 1000);
  renderLineChart("powerChart", "Wheel power (kW)", result.time_s, powerKw, "#d68910");
}

async function handleRunClick() {
  const errorEl = document.getElementById("errorMessage");
  errorEl.textContent = "";
  try {
    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      drive_cycle_name: readDriveCycleName(),
    };
    const result = await runSimulation(payload);
    renderSummary(result.summary);
    renderDynamicsCharts(result);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- Phase 3: ICE ----------

function renderIceSummary(summary) {
  document.getElementById("iceSumDistance").textContent = summary.distance_km.toFixed(3);
  document.getElementById("iceSumPeakTorque").textContent =
    summary.peak_engine_torque_nm.toFixed(1);
  document.getElementById("iceSumPeakPower").textContent =
    summary.peak_engine_power_kw.toFixed(2);
  document.getElementById("iceSumMaxRpm").textContent = summary.max_engine_rpm.toFixed(0);
  document.getElementById("iceSumFuelVolume").textContent =
    summary.total_fuel_volume_l.toFixed(3);
  document.getElementById("iceSumFuelConsumption").textContent =
    summary.avg_fuel_consumption_l_per_100km.toFixed(2);
}

function renderIceCharts(result) {
  renderLineChart(
    "engineTorqueChart", "Engine torque (N·m)", result.time_s,
    result.engine_torque_nm, "#8e44ad"
  );
  renderLineChart(
    "engineRpmChart", "Engine RPM", result.time_s, result.engine_rpm, "#2b6cb0"
  );
  const enginePowerKw = result.engine_power_w.map((p) => p / 1000);
  renderLineChart(
    "enginePowerChart", "Engine power (kW)", result.time_s, enginePowerKw, "#d68910"
  );
  const fuelPowerKw = result.fuel_power_w.map((p) => p / 1000);
  renderLineChart(
    "fuelPowerChart", "Fuel power (kW)", result.time_s, fuelPowerKw, "#c0392b"
  );
}

async function handleRunIceClick() {
  const errorEl = document.getElementById("errorMessage");
  errorEl.textContent = "";
  try {
    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      powertrain: readIcePowertrainParams(),
      drive_cycle_name: readDriveCycleName(),
    };
    const result = await runICESimulation(payload);
    renderIceSummary(result.summary);
    renderIceCharts(result);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- Phase 4: BEV ----------

function renderBevSummary(summary) {
  document.getElementById("bevSumDistance").textContent = summary.distance_km.toFixed(3);
  document.getElementById("bevSumPeakTorque").textContent =
    summary.peak_motor_torque_nm.toFixed(1);
  document.getElementById("bevSumPeakPower").textContent =
    summary.peak_motor_power_kw.toFixed(2);
  document.getElementById("bevSumFinalSoc").textContent = summary.final_soc_pct.toFixed(1);
  document.getElementById("bevSumTotalEnergy").textContent =
    summary.total_energy_kwh.toFixed(3);
  document.getElementById("bevSumRegenEnergy").textContent =
    summary.regen_energy_kwh.toFixed(3);
  document.getElementById("bevSumConsumption").textContent =
    summary.avg_consumption_kwh_per_100km.toFixed(2);
}

function renderBevCharts(result) {
  renderLineChart(
    "bevMotorTorqueChart", "Motor torque (N·m)", result.time_s,
    result.motor_torque_nm, "#8e44ad"
  );
  renderLineChart(
    "bevMotorRpmChart", "Motor RPM", result.time_s, result.motor_rpm, "#2b6cb0"
  );
  const batteryPowerKw = result.battery_power_w.map((p) => p / 1000);
  renderLineChart(
    "bevBatteryPowerChart", "Battery power (kW)", result.time_s, batteryPowerKw, "#d68910"
  );
  const socPct = result.soc.map((s) => s * 100);
  renderLineChart("bevSocChart", "SOC (%)", result.time_s, socPct, "#27ae60");
}

async function handleRunBevClick() {
  const errorEl = document.getElementById("errorMessage");
  errorEl.textContent = "";
  try {
    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      motor: readMotorParams(),
      battery: readBevBatteryParams(),
      drive_cycle_name: readDriveCycleName(),
    };
    const result = await runBEVSimulation(payload);
    renderBevSummary(result.summary);
    renderBevCharts(result);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- Phase 4: Hybrid ----------

function renderHybridSummary(summary) {
  document.getElementById("hybridSumDistance").textContent = summary.distance_km.toFixed(3);
  document.getElementById("hybridSumPeakIceTorque").textContent =
    summary.peak_ice_torque_nm.toFixed(1);
  document.getElementById("hybridSumPeakMotorTorque").textContent =
    summary.peak_motor_torque_nm.toFixed(1);
  document.getElementById("hybridSumFinalSoc").textContent =
    summary.final_soc_pct.toFixed(1);
  document.getElementById("hybridSumFuelVolume").textContent =
    summary.total_fuel_volume_l.toFixed(3);
  document.getElementById("hybridSumRegenEnergy").textContent =
    summary.regen_energy_kwh.toFixed(3);
  document.getElementById("hybridSumFuelConsumption").textContent =
    summary.avg_fuel_consumption_l_per_100km.toFixed(2);
}

function renderHybridCharts(result) {
  renderLineChart(
    "hybridIceTorqueChart", "ICE torque (N·m)", result.time_s,
    result.ice_torque_nm, "#c0392b"
  );
  renderLineChart(
    "hybridMotorTorqueChart", "Motor torque (N·m)", result.time_s,
    result.motor_torque_nm, "#8e44ad"
  );
  const batteryPowerKw = result.battery_power_w.map((p) => p / 1000);
  renderLineChart(
    "hybridBatteryPowerChart", "Battery power (kW)", result.time_s,
    batteryPowerKw, "#d68910"
  );
  const socPct = result.soc.map((s) => s * 100);
  renderLineChart("hybridSocChart", "SOC (%)", result.time_s, socPct, "#27ae60");
}

async function handleRunHybridClick() {
  const errorEl = document.getElementById("errorMessage");
  errorEl.textContent = "";
  try {
    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      ice: readIcePowertrainParams(),
      motor: readMotorParams(),
      battery: readHybridBatteryParams(),
      electric_only_power_threshold_w:
        parseFloat(document.getElementById("electricOnlyThreshold").value) * 1000,
      motor_assist_fraction: parseFloat(
        document.getElementById("motorAssistFraction").value
      ),
      drive_cycle_name: readDriveCycleName(),
    };
    const result = await runHybridSimulation(payload);
    renderHybridSummary(result.summary);
    renderHybridCharts(result);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- Drive cycle list ----------

async function populateDriveCycles() {
  try {
    const cycles = await listDriveCycles();
    const select = document.getElementById("driveCycleSelect");
    select.innerHTML = "";
    cycles.forEach((name) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      select.appendChild(option);
    });
  } catch (err) {
    console.warn("Could not load drive cycles from API:", err.message);
  }
}

document.getElementById("runBtn").addEventListener("click", handleRunClick);
document.getElementById("runIceBtn").addEventListener("click", handleRunIceClick);
document.getElementById("runBevBtn").addEventListener("click", handleRunBevClick);
document.getElementById("runHybridBtn").addEventListener("click", handleRunHybridClick);
populateDriveCycles();