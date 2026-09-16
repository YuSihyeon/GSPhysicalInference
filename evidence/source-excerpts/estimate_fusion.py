"""Small, explicit fusion rules for the physical-twin pilot."""

from __future__ import annotations

import math


def validate_measurement(*, status: str, residual: float, residual_limit: float) -> bool:
    """Fail closed unless both the trial status and residual gate pass."""

    return (
        status == "completed"
        and math.isfinite(float(residual))
        and 0.0 <= float(residual) <= float(residual_limit)
    )


def fuse_scalar(*, prior_value: float, measurement_value: float, measurement_weight: float) -> float:
    """Convex combination used only after measurement validation."""

    values = (float(prior_value), float(measurement_value), float(measurement_weight))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("fusion inputs must be finite")
    if not 0.0 <= values[2] <= 1.0:
        raise ValueError("measurement weight must lie in [0, 1]")
    return (1.0 - values[2]) * values[0] + values[2] * values[1]
