"""
Real-world vehicle data handling.

Loads a CSV of real (measured) vehicle data and exposes it in a form
the simulation engine can consume:
    - time_s, speed_mps -> used to build a DriveCycle (drives the model)
    - any additional numeric columns (e.g. real SOC, real fuel volume)
      -> kept as reference data for validation against model output

Expected CSV columns (header row required):
    time_s      : time in seconds (required)
    speed_kmh    : vehicle speed in km/h (required)
    soc          : optional, real battery SOC in [0, 1]
    fuel_l       : optional, real cumulative fuel volume in liters
    (other numeric columns are kept as-is under 'extra_columns')
"""

from dataclasses import dataclass, field
from io import StringIO

import numpy as np
import pandas as pd

from app.simulation.drive_cycle import DriveCycle

REQUIRED_COLUMNS = {"time_s", "speed_kmh"}
KNOWN_REFERENCE_COLUMNS = {"soc", "fuel_l"}


@dataclass
class RealVehicleData:
    """
    Parsed real-world vehicle data.

    Attributes:
        time_s: Time stamps [s]
        speed_mps: Measured speed [m/s]
        reference_columns: Dict of column name -> numpy array, for any
            known reference columns present in the CSV (soc, fuel_l)
        extra_columns: Dict of column name -> numpy array, for any
            other numeric columns present but not specifically used
        source_name: Label for this dataset (e.g. original filename)
    """

    time_s: np.ndarray
    speed_mps: np.ndarray
    reference_columns: dict = field(default_factory=dict)
    extra_columns: dict = field(default_factory=dict)
    source_name: str = "uploaded_data"

    def to_drive_cycle(self) -> DriveCycle:
        """Build a DriveCycle from this dataset's time/speed, to drive the model."""
        return DriveCycle(
            time_s=self.time_s, speed_mps=self.speed_mps, name=self.source_name
        )

    def has_reference(self, column: str) -> bool:
        return column in self.reference_columns

    def get_reference(self, column: str) -> np.ndarray:
        if column not in self.reference_columns:
            raise KeyError(f"Reference column '{column}' not found in real data.")
        return self.reference_columns[column]


def parse_real_data_csv(csv_text: str, source_name: str = "uploaded_data") -> RealVehicleData:
    """
    Parse CSV text into a RealVehicleData instance.

    Raises ValueError if required columns are missing or data is invalid.
    """
    try:
        df = pd.read_csv(StringIO(csv_text))
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

    if len(df) < 2:
        raise ValueError("CSV must contain at least 2 data rows.")

    df = df.sort_values("time_s").reset_index(drop=True)

    time_s = df["time_s"].to_numpy(dtype=float)
    speed_mps = df["speed_kmh"].to_numpy(dtype=float) / 3.6

    if np.any(np.diff(time_s) <= 0):
        raise ValueError("time_s column must be strictly increasing.")

    reference_columns = {}
    extra_columns = {}

    for col in df.columns:
        if col in REQUIRED_COLUMNS:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        values = df[col].to_numpy(dtype=float)
        if col in KNOWN_REFERENCE_COLUMNS:
            reference_columns[col] = values
        else:
            extra_columns[col] = values

    return RealVehicleData(
        time_s=time_s,
        speed_mps=speed_mps,
        reference_columns=reference_columns,
        extra_columns=extra_columns,
        source_name=source_name,
    )


def preview_real_data(data: RealVehicleData, max_points: int = 20) -> dict:
    """
    Build a lightweight preview (subsampled) of the parsed data, for
    the frontend to show before running a full validation.
    """
    n = len(data.time_s)
    step = max(1, n // max_points)
    idx = list(range(0, n, step))

    return {
        "source_name": data.source_name,
        "num_points": n,
        "duration_s": float(data.time_s[-1] - data.time_s[0]),
        "max_speed_kmh": float(np.max(data.speed_mps)) * 3.6,
        "available_reference_columns": list(data.reference_columns.keys()),
        "preview_time_s": [float(data.time_s[i]) for i in idx],
        "preview_speed_kmh": [float(data.speed_mps[i] * 3.6) for i in idx],
    }