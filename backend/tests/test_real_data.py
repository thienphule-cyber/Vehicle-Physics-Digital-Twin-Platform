"""
Tests for Phase 7 - real data parsing and validation metrics.
"""

import numpy as np
import pytest

from app.simulation.real_data import parse_real_data_csv, preview_real_data
from app.analysis.validation import (
    interpolate_to_grid,
    mean_absolute_error,
    root_mean_squared_error,
    max_absolute_error,
    compare_series,
)


SAMPLE_CSV = """time_s,speed_kmh,soc
0,0,0.80
1,10,0.799
2,20,0.797
3,30,0.794
4,40,0.790
"""


def test_parse_real_data_csv_basic():
    data = parse_real_data_csv(SAMPLE_CSV, source_name="test.csv")

    assert len(data.time_s) == 5
    assert data.speed_mps[1] == pytest.approx(10 / 3.6, rel=1e-6)
    assert data.has_reference("soc")
    assert data.get_reference("soc")[0] == pytest.approx(0.80)


def test_parse_real_data_csv_missing_required_column_raises():
    bad_csv = "time_s,soc\n0,0.8\n1,0.79\n"
    with pytest.raises(ValueError):
        parse_real_data_csv(bad_csv)


def test_parse_real_data_csv_non_increasing_time_raises():
    bad_csv = "time_s,speed_kmh\n0,0\n0,10\n1,20\n"
    with pytest.raises(ValueError):
        parse_real_data_csv(bad_csv)


def test_preview_real_data_contains_expected_keys():
    data = parse_real_data_csv(SAMPLE_CSV)
    preview = preview_real_data(data, max_points=3)

    expected_keys = {
        "source_name",
        "num_points",
        "duration_s",
        "max_speed_kmh",
        "available_reference_columns",
        "preview_time_s",
        "preview_speed_kmh",
    }
    assert expected_keys.issubset(preview.keys())
    assert "soc" in preview["available_reference_columns"]


def test_interpolate_to_grid_matches_at_known_points():
    source_time = np.array([0.0, 1.0, 2.0])
    source_values = np.array([10.0, 20.0, 30.0])
    target_time = np.array([0.0, 0.5, 1.0, 2.0])

    result = interpolate_to_grid(source_time, source_values, target_time)

    assert result[0] == pytest.approx(10.0)
    assert result[1] == pytest.approx(15.0)
    assert result[2] == pytest.approx(20.0)
    assert result[3] == pytest.approx(30.0)


def test_error_metrics_zero_for_identical_series():
    model = np.array([1.0, 2.0, 3.0])
    real = np.array([1.0, 2.0, 3.0])

    assert mean_absolute_error(model, real) == pytest.approx(0.0)
    assert root_mean_squared_error(model, real) == pytest.approx(0.0)
    assert max_absolute_error(model, real) == pytest.approx(0.0)


def test_error_metrics_nonzero_for_offset_series():
    model = np.array([1.0, 2.0, 3.0])
    real = np.array([1.5, 2.5, 3.5])

    assert mean_absolute_error(model, real) == pytest.approx(0.5)
    assert max_absolute_error(model, real) == pytest.approx(0.5)


def test_compare_series_returns_expected_structure():
    model_time = np.array([0.0, 1.0, 2.0])
    model_values = np.array([10.0, 20.0, 30.0])
    real_time = np.array([0.0, 1.0, 2.0])
    real_values = np.array([11.0, 19.0, 31.0])

    result = compare_series(model_time, model_values, real_time, real_values)

    expected_keys = {
        "time_s", "model_values", "real_values", "error",
        "mae", "rmse", "max_error", "bias",
    }
    assert expected_keys.issubset(result.keys())
    assert result["mae"] == pytest.approx(1.0)