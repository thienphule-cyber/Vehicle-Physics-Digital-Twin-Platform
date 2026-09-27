/**
 * Page logic for comparison.html (Phase 8).
 *
 * Reads shared vehicle/environment/drive-cycle inputs plus
 * per-powertrain parameters, runs the unified comparison endpoint,
 * and renders a 3-column metric table plus overlay charts (torque,
 * battery power, SOC) so ICE/Hybrid/BEV can be compared directly.
 */

let comparisonCharts = {};

// ---------- Input readers ----------

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
    capacity_wh: parseFloat(document.getElementById("bevBatteryCapacity").value) * 1000,
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

// ---------- Table rendering ----------

const METRIC_LABELS = {
  distance_km: "Distance (km)",
  max_speed_kmh: "Max speed (km/h)",
  overall_efficiency_pct: "Overall efficiency (%)",
  fuel_used_l: "Fuel used (L)",
  energy_used_kwh: "Energy used (kWh)",
  regen_energy_kwh: "Regen energy (kWh)",
  final_soc_pct: "Final SOC (%)",
};

const METRIC_DECIMALS = {
  distance_km: 3,
  max_speed_kmh: 1,
  overall_efficiency_pct: 1,
  fuel_used_l: 3,
  energy_used_kwh: 3,
  regen_energy_kwh: 3,
  final_soc_pct: 1,
};

function formatMetricValue(value, decimals) {
  if (value === null || value === undefined) return "—";
  return value.toFixed(decimals);
}

function renderComparisonTable(table) {
  const tbody = document.getElementById("comparisonTableBody");
  tbody.innerHTML = "";

  Object.keys(METRIC_LABELS).forEach((metricKey) => {
    const row = table[metricKey];
    if (!row) return;

    const decimals = METRIC_DECIMALS[metricKey] ?? 2;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${METRIC_LABELS[metricKey]}</td>
      <td>${formatMetricValue(row.ice, decimals)}</td>
      <td>${formatMetricValue(row.hybrid, decimals)}</td>
      <td>${formatMetricValue(row.bev, decimals)}</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById("comparison-table-section").style.display = "block";
}

// ---------- Chart rendering ----------

function renderMultiLineChart(canvasId, timeS, series, yTitle) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  if (comparisonCharts[canvasId]) {
    comparisonCharts[canvasId].destroy();
  }

  const datasets = series.map((s) => ({
    label: s.label,
    data: timeS.map((t, i) => ({ x: t, y: s.values[i] })),
    borderColor: s.color,
    backgroundColor: s.color,
    borderWidth: 1.5,
    pointRadius: 0,
    tension: 0.1,
  }));

  comparisonCharts[canvasId] = new Chart(ctx, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      animation: false,
      parsing: false,
      scales: {
        x: { type: "linear", title: { display: true, text: "Time (s)" } },
        y: { title: { display: true, text: yTitle } },
      },
      plugins: {
        legend: { display: true },
      },
    },
  });
}

function renderComparisonCharts(result) {
  const timeS = result.time_s;

  renderMultiLineChart(
    "torqueCompareChart",
    timeS,
    [
      { label: "ICE engine torque (N·m)", values: result.ice_result.engine_torque_nm, color: "#c0392b" },
      { label: "Hybrid ICE torque (N·m)", values: result.hybrid_result.ice_torque_nm, color: "#e67e22" },
      { label: "Hybrid motor torque (N·m)", values: result.hybrid_result.motor_torque_nm, color: "#8e44ad" },
      { label: "BEV motor torque (N·m)", values: result.bev_result.motor_torque_nm, color: "#2b6cb0" },
    ],
    "Torque (N·m)"
  );

  const hybridBatteryKw = result.hybrid_result.battery_power_w.map((p) => p / 1000);
  const bevBatteryKw = result.bev_result.battery_power_w.map((p) => p / 1000);

  renderMultiLineChart(
    "batteryPowerCompareChart",
    timeS,
    [
      { label: "Hybrid battery power (kW)", values: hybridBatteryKw, color: "#8e44ad" },
      { label: "BEV battery power (kW)", values: bevBatteryKw, color: "#2b6cb0" },
    ],
    "Battery power (kW)"
  );

  const hybridSocPct = result.hybrid_result.soc.map((s) => s * 100);
  const bevSocPct = result.bev_result.soc.map((s) => s * 100);

  renderMultiLineChart(
    "socCompareChart",
    timeS,
    [
      { label: "Hybrid SOC (%)", values: hybridSocPct, color: "#8e44ad" },
      { label: "BEV SOC (%)", values: bevSocPct, color: "#2b6cb0" },
    ],
    "SOC (%)"
  );

  document.getElementById("comparison-charts").style.display = "block";
}

// ---------- Run comparison ----------

async function handleRunComparisonClick() {
  const errorEl = document.getElementById("errorMessage");
  errorEl.textContent = "";

  try {
    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      drive_cycle_name: readDriveCycleName(),
      ice: readIcePowertrainParams(),
      motor: readMotorParams(),
      bev_battery: readBevBatteryParams(),
      hybrid_battery: readHybridBatteryParams(),
      electric_only_power_threshold_w:
        parseFloat(document.getElementById("electricOnlyThreshold").value) * 1000,
      motor_assist_fraction: parseFloat(
        document.getElementById("motorAssistFraction").value
      ),
    };

    const result = await runComparison(payload);

    renderComparisonTable(result.comparison_table);
    renderComparisonCharts(result);
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

document.getElementById("runComparisonBtn").addEventListener("click", handleRunComparisonClick);
populateDriveCycles();