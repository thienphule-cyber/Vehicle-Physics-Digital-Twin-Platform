"""
Model vs real-data validation metrics.

Computes standard error metrics (MAE, RMSE, max error) between a
model-predicted time-series and a real (measured) time-series,
interpolating the real data onto the model's time grid when their
sampling does not match exactly.
"""

import numpy as np


def interpolate_to_grid(
    source_time_s: np.ndarray, source_values: np.ndarray, target_time_s: np.ndarray
) -> np.ndarray:
    """
    Linearly interpolate source_values (sampled at source_time_s) onto
    target_time_s. Values outside the source time range are clamped
    to the nearest edge value (no extrapolation).
    """
    return np.interp(target_time_s, source_time_s, source_values)


def mean_absolute_error(model: np.ndarray, real: np.ndarray) -> float:
    """MAE = mean(|model - real|)."""
    return float(np.mean(np.abs(model - real)))


def root_mean_squared_error(model: np.ndarray, real: np.ndarray) -> float:
    """RMSE = sqrt(mean((model - real)^2))."""
    return float(np.sqrt(np.mean((model - real) ** 2)))


def max_absolute_error(model: np.ndarray, real: np.ndarray) -> float:
    """Maximum absolute error over the whole series."""
    return float(np.max(np.abs(model - real)))


def mean_error(model: np.ndarray, real: np.ndarray) -> float:
    """Signed mean error (bias): mean(model - real)."""
    return float(np.mean(model - real))


def compare_series(
    model_time_s: np.ndarray,
    model_values: np.ndarray,
    real_time_s: np.ndarray,
    real_values: np.ndarray,
) -> dict:
    """
    Compare a model time-series against real (measured) data,
    interpolating the real data onto the model's time grid.

    Returns a dict with:
        time_s: model time grid (list)
        model_values: model values (list)
        real_values: real values interpolated onto model grid (list)
        error: model - real at each point (list)
        mae, rmse, max_error, mean_error (bias): scalar metrics
    """
    real_on_model_grid = interpolate_to_grid(real_time_s, real_values, model_time_s)
    error = model_values - real_on_model_grid

    return {
        "time_s": model_time_s.tolist(),
        "model_values": model_values.tolist(),
        "real_values": real_on_model_grid.tolist(),
        "error": error.tolist(),
        "mae": mean_absolute_error(model_values, real_on_model_grid),
        "rmse": root_mean_squared_error(model_values, real_on_model_grid),
        "max_error": max_absolute_error(model_values, real_on_model_grid),
        "bias": mean_error(model_values, real_on_model_grid),
    }