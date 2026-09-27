/**
 * Page logic for validation.html (Phase 7).
 *
 * Handles CSV upload (file or pasted text), preview, and running
 * BEV/ICE validation against the uploaded real data, rendering
 * comparison charts and error metrics.
 */

let validationCharts = {};
let currentCsvText = null;

// ---------- CSV input handling ----------

function readCsvTextInput() {
  const fileInput = document.getElementById("csvFileInput");
  const textInput = document.getElementById("csvTextInput");

  if (fileInput.files.length > 0) {
    return null; // handled asynchronously via FileReader, see handlePreviewClick
  }
  return textInput.value.trim() || null;
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Could not read the selected file."));
    reader.readAsText(file);
  });
}

async function getCsvText() {
  const fileInput = document.getElementById("csvFileInput");
  if (fileInput.files.length > 0) {
    return await readFileAsText(fileInput.files[0]);
  }

  const textInput = document.getElementById("csvTextInput");
  const text = textInput.value.trim();
  if (!text) {
    throw new Error("Please upload a CSV file or paste CSV text.");
  }
  return text;
}

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

function readBatteryParams() {
  return {
    capacity_wh: parseFloat(document.getElementById("batteryCapacityBev").value) * 1000,
    initial_soc: parseFloat(document.getElementById("batteryInitialSoc").value),
    min_soc: parseFloat(document.getElementById("batteryMinSoc").value),
    max_soc: parseFloat(document.getElementById("batteryMaxSoc").value),
    internal_efficiency: parseFloat(document.getElementById("batteryInternalEff").value),
  };
}

// ---------- Chart helpers ----------

function renderLineChart(canvasId, datasets, yTitle) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  if (validationCharts[canvasId]) {
    validationCharts[canvasId].destroy();
  }

  validationCharts[canvasId] = new Chart(ctx, {
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

// ---------- Preview ----------

async function handlePreviewClick() {
  const errorEl = document.getElementById("uploadError");
  errorEl.textContent = "";

  try {
    const csvText = await getCsvText();
    currentCsvText = csvText;

    const preview = await uploadRealData({ csv_text: csvText, source_name: "uploaded_data" });

    document.getElementById("prevSource").textContent = preview.source_name;
    document.getElementById("prevPoints").textContent = preview.num_points;
    document.getElementById("prevDuration").textContent = preview.duration_s.toFixed(1);
    document.getElementById("prevMaxSpeed").textContent = preview.max_speed_kmh.toFixed(1);
    document.getElementById("prevRefColumns").textContent =
      preview.available_reference_columns.length > 0
        ? preview.available_reference_columns.join(", ")
        : "(none)";

    document.getElementById("preview-section").style.display = "block";

    renderLineChart(
      "previewSpeedChart",
      [
        {
          label: "Speed (km/h)",
          data: preview.preview_time_s.map((t, i) => ({
            x: t,
            y: preview.preview_speed_kmh[i],
          })),
          borderColor: "#2b6cb0",
          backgroundColor: "#2b6cb0",
          pointRadius: 0,
          borderWidth: 1.5,
        },
      ],
      "Speed (km/h)"
    );
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- Validation rendering (shared) ----------

function renderValidationResult(result) {
  const c = result.comparison;

  document.getElementById("valQuantity").textContent = result.quantity;
  document.getElementById("valMae").textContent = c.mae.toFixed(5);
  document.getElementById("valRmse").textContent = c.rmse.toFixed(5);
  document.getElementById("valMaxError").textContent = c.max_error.toFixed(5);
  document.getElementById("valBias").textContent = c.bias.toFixed(5);

  document.getElementById("validation-summary").style.display = "block";
  document.getElementById("validation-charts").style.display = "block";

  renderLineChart(
    "modelVsRealChart",
    [
      {
        label: "Model",
        data: c.time_s.map((t, i) => ({ x: t, y: c.model_values[i] })),
        borderColor: "#2b6cb0",
        backgroundColor: "#2b6cb0",
        pointRadius: 0,
        borderWidth: 1.5,
      },
      {
        label: "Real (measured)",
        data: c.time_s.map((t, i) => ({ x: t, y: c.real_values[i] })),
        borderColor: "#c0392b",
        backgroundColor: "#c0392b",
        pointRadius: 0,
        borderWidth: 1.5,
        borderDash: [5, 4],
      },
    ],
    result.quantity
  );

  renderLineChart(
    "errorChart",
    [
      {
        label: "Error (model - real)",
        data: c.time_s.map((t, i) => ({ x: t, y: c.error[i] })),
        borderColor: "#d68910",
        backgroundColor: "#d68910",
        pointRadius: 0,
        borderWidth: 1.5,
      },
    ],
    "Error"
  );
}

// ---------- BEV validation ----------

async function handleValidateBevClick() {
  const errorEl = document.getElementById("validationError");
  errorEl.textContent = "";

  try {
    if (!currentCsvText) {
      currentCsvText = await getCsvText();
    }

    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      motor: readMotorParams(),
      battery: readBatteryParams(),
      csv_text: currentCsvText,
      source_name: "uploaded_data",
    };

    const result = await validateBev(payload);
    renderValidationResult(result);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

// ---------- ICE validation ----------

async function handleValidateIceClick() {
  const errorEl = document.getElementById("validationError");
  errorEl.textContent = "";

  try {
    if (!currentCsvText) {
      currentCsvText = await getCsvText();
    }

    const payload = {
      vehicle: readVehicleParams(),
      environment: readEnvironmentParams(),
      powertrain: readIcePowertrainParams(),
      csv_text: currentCsvText,
      source_name: "uploaded_data",
    };

    const result = await validateIce(payload);
    renderValidationResult(result);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

document.getElementById("previewBtn").addEventListener("click", handlePreviewClick);
document.getElementById("validateBevBtn").addEventListener("click", handleValidateBevClick);
document.getElementById("validateIceBtn").addEventListener("click", handleValidateIceClick);