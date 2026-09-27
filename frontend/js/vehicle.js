/**
 * Page logic for vehicle.html (Phase 1).
 *
 * Reads form inputs, calls the API via api.js, and renders the
 * returned force/torque/power breakdown into the results table.
 */

function readVehicleForm() {
  return {
    mass: parseFloat(document.getElementById("mass").value),
    wheel_radius: parseFloat(document.getElementById("wheelRadius").value),
    drag_coefficient: parseFloat(document.getElementById("dragCoefficient").value),
    frontal_area: parseFloat(document.getElementById("frontalArea").value),
    rolling_resistance_coefficient: parseFloat(
      document.getElementById("rollingCoefficient").value
    ),
    air_density: parseFloat(document.getElementById("airDensity").value),
    road_grade_deg: parseFloat(document.getElementById("roadGradeDeg").value),
    wind_speed: parseFloat(document.getElementById("windSpeed").value),
    velocity: parseFloat(document.getElementById("velocity").value),
    acceleration: parseFloat(document.getElementById("acceleration").value),
  };
}

function renderResults(result) {
  document.getElementById("resFRolling").textContent = result.f_rolling.toFixed(2);
  document.getElementById("resFAero").textContent = result.f_aero.toFixed(2);
  document.getElementById("resFGrade").textContent = result.f_grade.toFixed(2);
  document.getElementById("resFAcc").textContent = result.f_acc.toFixed(2);
  document.getElementById("resFTraction").textContent = result.f_traction.toFixed(2);
  document.getElementById("resTorque").textContent = result.wheel_torque_nm.toFixed(2);
  document.getElementById("resPower").textContent = result.wheel_power_kw.toFixed(2);
}

async function handleCalculateClick() {
  const errorEl = document.getElementById("errorMessage");
  errorEl.textContent = "";

  try {
    const payload = readVehicleForm();
    const result = await checkPhysics(payload);
    renderResults(result);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
  }
}

document
  .getElementById("calculateBtn")
  .addEventListener("click", handleCalculateClick);