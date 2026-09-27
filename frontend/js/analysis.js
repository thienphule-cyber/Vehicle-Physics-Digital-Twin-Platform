/**
 * Page logic for analysis.html (Phase 5).
 *
 * Reads the same vehicle/environment/powertrain inputs as
 * simulation.html, calls the energy-breakdown API endpoints, and
 * renders both a summary table and a bar chart (input vs useful
 * energy vs losses) for each powertrain.
 */

let analysisCharts = {};

// ---------- Shared input readers (same shape as simulation.js) ----------

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

// ---------- Chart helper: energy flow bar chart ----------

function renderEnergyBarChart(canvasId, labels, values, colors) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  if (analysisCharts[canvasId]) {
    analysisCharts[canvasId].destroy();
  }

  analysisCharts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Energy (kWh)",
          data: values,
          backgroundColor: colors,
        },
      ],
    },
    options: {
      responsive: true,
      animation: false,
      plugins: {
        legend: { display: false },
        title: { display: true, text: "Energy flow (kWh)" },
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "kWh" } },
      },
    },
  });
}

// ---------- ICE analysis ----------

function renderIceAnalysis(breakdown) {
  document.getElementById("iceFuelEnergy").textContent =
    breakdown.fuel_energy_kwh.toFixed(3);
  document.getElementById("iceEngineEnergy").textContent =
    breakdown.engine_mechanical_energy_kwh.toFixed(3);
  document.getElementById("iceWheelEnergy").textContent =
    breakdown.wheel_energy_kwh.toFixed(3);
  document.getElementById("iceEngineEfficiency").textContent =
    breakdown.engine_efficiency_pct.toFixed(1);
  document.getElementById("iceTransEfficiency").textContent =
    breakdown.transmission_efficiency_pct.toFixed(1);
  document.getElementById("iceOverallEfficiency").textContent =
    breakdown.overall_efficiency_pct.toFixed(1);

  renderEnergyBarChart(
    "iceEnergyChart",
    ["Fuel energy", "Engine mechanical", "Wheel energy"],
    [
      breakdown.fuel_energy_kwh,
      breakdown.engine_mechanical_energy_kwh,
      breakdown.wheel_energy_kwh,
    ],
    ["#c0392b", "#8e44ad", "#2b6cb0"]
  );
}

async function handleAnalyzeIceClick() {
  const errorEl = document.getElementById("errorMessage");
  errorEl.textContent = "";
  try {
    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      powertrain: readIcePowertrainParams(),
      drive_cycle_name: readDriveCycleName(),
    };
    const breakdown = await analyzeIceEnergy(payload);
    renderIceAnalysis(breakdown);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- BEV analysis ----------

function renderBevAnalysis(breakdown) {
  document.getElementById("bevDischargeEnergy").textContent =
    breakdown.battery_discharge_energy_kwh.toFixed(3);
  document.getElementById("bevRegenEnergy").textContent =
    breakdown.regen_energy_kwh.toFixed(3);
  document.getElementById("bevMotorEnergy").textContent =
    breakdown.motor_mechanical_energy_kwh.toFixed(3);
  document.getElementById("bevWheelEnergy").textContent =
    breakdown.wheel_energy_kwh.toFixed(3);
  document.getElementById("bevMotorEfficiency").textContent =
    breakdown.motor_efficiency_pct.toFixed(1);
  document.getElementById("bevOverallEfficiency").textContent =
    breakdown.overall_efficiency_pct.toFixed(1);

  renderEnergyBarChart(
    "bevEnergyChart",
    ["Battery discharge", "Regen", "Motor mechanical", "Wheel energy"],
    [
      breakdown.battery_discharge_energy_kwh,
      breakdown.regen_energy_kwh,
      breakdown.motor_mechanical_energy_kwh,
      breakdown.wheel_energy_kwh,
    ],
    ["#d68910", "#27ae60", "#8e44ad", "#2b6cb0"]
  );
}

async function handleAnalyzeBevClick() {
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
    const breakdown = await analyzeBevEnergy(payload);
    renderBevAnalysis(breakdown);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- Hybrid analysis ----------

function renderHybridAnalysis(breakdown) {
  document.getElementById("hybridFuelEnergy").textContent =
    breakdown.fuel_energy_kwh.toFixed(3);
  document.getElementById("hybridDischargeEnergy").textContent =
    breakdown.battery_discharge_energy_kwh.toFixed(3);
  document.getElementById("hybridRegenEnergy").textContent =
    breakdown.regen_energy_kwh.toFixed(3);
  document.getElementById("hybridIceEnergy").textContent =
    breakdown.ice_mechanical_energy_kwh.toFixed(3);
  document.getElementById("hybridMotorEnergy").textContent =
    breakdown.motor_mechanical_energy_kwh.toFixed(3);
  document.getElementById("hybridWheelEnergy").textContent =
    breakdown.wheel_energy_kwh.toFixed(3);
  document.getElementById("hybridOverallEfficiency").textContent =
    breakdown.overall_efficiency_pct.toFixed(1);

  renderEnergyBarChart(
    "hybridEnergyChart",
    ["Fuel energy", "Battery discharge", "Regen", "ICE mech.", "Motor mech.", "Wheel"],
    [
      breakdown.fuel_energy_kwh,
      breakdown.battery_discharge_energy_kwh,
      breakdown.regen_energy_kwh,
      breakdown.ice_mechanical_energy_kwh,
      breakdown.motor_mechanical_energy_kwh,
      breakdown.wheel_energy_kwh,
    ],
    ["#c0392b", "#d68910", "#27ae60", "#e67e22", "#8e44ad", "#2b6cb0"]
  );
}

async function handleAnalyzeHybridClick() {
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
    const breakdown = await analyzeHybridEnergy(payload);
    renderHybridAnalysis(breakdown);
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

document.getElementById("analyzeIceBtn").addEventListener("click", handleAnalyzeIceClick);
document.getElementById("analyzeBevBtn").addEventListener("click", handleAnalyzeBevClick);
document
  .getElementById("analyzeHybridBtn")
  .addEventListener("click", handleAnalyzeHybridClick);
populateDriveCycles();