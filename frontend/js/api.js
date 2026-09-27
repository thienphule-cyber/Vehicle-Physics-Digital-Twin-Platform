/**
 * API service layer.
 *
 * Centralizes all HTTP calls to the backend. Page-specific scripts
 * (vehicle.js, simulation.js, analysis.js, comparison.js,
 * validation.js) call functions from this file instead of using
 * fetch() directly.
 */

async function apiGet(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(
      errorBody?.detail
        ? JSON.stringify(errorBody.detail)
        : `Request failed with status ${response.status}`
    );
  }

  return response.json();
}

async function apiPost(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(
      errorBody?.detail
        ? JSON.stringify(errorBody.detail)
        : `Request failed with status ${response.status}`
    );
  }

  return response.json();
}

async function checkPhysics(payload) {
  return apiPost("/api/vehicles/check-physics", payload);
}

async function listDriveCycles() {
  return apiGet("/api/simulation/drive-cycles");
}

async function runSimulation(payload) {
  return apiPost("/api/simulation/run", payload);
}

async function runICESimulation(payload) {
  return apiPost("/api/simulation/run-ice", payload);
}

async function runBEVSimulation(payload) {
  return apiPost("/api/simulation/run-bev", payload);
}

async function runHybridSimulation(payload) {
  return apiPost("/api/simulation/run-hybrid", payload);
}

async function analyzeIceEnergy(payload) {
  return apiPost("/api/analysis/energy-ice", payload);
}

async function analyzeBevEnergy(payload) {
  return apiPost("/api/analysis/energy-bev", payload);
}

async function analyzeHybridEnergy(payload) {
  return apiPost("/api/analysis/energy-hybrid", payload);
}

async function uploadRealData(payload) {
  return apiPost("/api/validation/upload", payload);
}

async function validateBev(payload) {
  return apiPost("/api/validation/validate-bev", payload);
}

async function validateIce(payload) {
  return apiPost("/api/validation/validate-ice", payload);
}

/**
 * Phase 8: run ICE, Hybrid and BEV simulations together under
 * identical conditions and return a unified comparison.
 */
async function runComparison(payload) {
  return apiPost("/api/comparison/run", payload);
}