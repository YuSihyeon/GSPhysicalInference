"""Paired statistics that treat physical worlds, not frames, as replicates."""

from __future__ import annotations

from itertools import product
from typing import Iterable, Mapping

import numpy as np


def prediction_curve_auc(values: Iterable[float]) -> float:
    curve = np.asarray(tuple(values), dtype=np.float64)
    if curve.ndim != 1 or len(curve) < 2 or not np.all(np.isfinite(curve)):
        raise ValueError("prediction curve must contain at least two finite values")
    return float(np.trapz(curve, dx=1.0))


def _paired_differences(left: Iterable[float], right: Iterable[float]) -> np.ndarray:
    left_values = np.asarray(tuple(left), dtype=np.float64)
    right_values = np.asarray(tuple(right), dtype=np.float64)
    if left_values.shape != right_values.shape or left_values.ndim != 1 or not len(left_values):
        raise ValueError("paired samples must be non-empty one-dimensional arrays of equal length")
    if not np.all(np.isfinite(left_values)) or not np.all(np.isfinite(right_values)):
        raise ValueError("paired samples must be finite")
    return left_values - right_values


def paired_bootstrap_ci(
    left: Iterable[float],
    right: Iterable[float],
    seed: int,
    samples: int = 10_000,
) -> tuple[float, float]:
    differences = _paired_differences(left, right)
    if samples <= 0:
        raise ValueError("samples must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(differences), size=(samples, len(differences)))
    bootstrap_means = differences[indices].mean(axis=1)
    low, high = np.percentile(bootstrap_means, [2.5, 97.5])
    return float(low), float(high)


def sign_flip_pvalue(differences: Iterable[float]) -> float:
    values = np.asarray(tuple(differences), dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)):
        raise ValueError("differences must be a non-empty finite vector")
    nonzero = values[values != 0.0]
    if not len(nonzero):
        return 1.0
    if len(nonzero) > 20:
        raise ValueError("exact sign-flip test supports at most 20 non-zero pairs")
    observed = abs(float(np.mean(nonzero)))
    extreme = 0
    total = 2 ** len(nonzero)
    for signs in product((-1.0, 1.0), repeat=len(nonzero)):
        statistic = abs(float(np.mean(nonzero * np.asarray(signs))))
        if statistic >= observed - 1e-15:
            extreme += 1
    return extreme / total


def summarize_paired_results(rows: Iterable[Mapping[str, float]], seed: int) -> dict[str, object]:
    records = tuple(rows)
    if not records:
        raise ValueError("at least one independent unit is required")
    unit_ids = [str(record["unit_id"]) for record in records]
    if len(set(unit_ids)) != len(unit_ids):
        raise ValueError("unit_id values must be unique")
    fixed = np.asarray([float(record["fixed_active_auc"]) for record in records])
    adaptive = np.asarray([float(record["adaptive_active_auc"]) for record in records])
    differences = _paired_differences(fixed, adaptive)
    return {
        "independent_units": len(records),
        "contrast": "fixed_active_auc - adaptive_active_auc",
        "mean_fixed_minus_adaptive": float(np.mean(differences)),
        "median_fixed_minus_adaptive": float(np.median(differences)),
        "paired_bootstrap_ci95": list(paired_bootstrap_ci(fixed, adaptive, seed=seed)),
        "exact_sign_flip_pvalue_two_sided": sign_flip_pvalue(differences),
    }

