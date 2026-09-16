"""Particle belief over rigid-body mass, friction, and restitution."""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
from scipy.special import logsumexp

from .actions import Action


PARAMETER_BOUNDS = np.asarray(
    [
        [0.20, 2.00],
        [0.15, 0.90],
        [0.10, 0.80],
        [0.05, 0.85],
    ],
    dtype=np.float64,
)


@dataclass(frozen=True)
class ParameterSummary:
    mass_kg: float
    static_friction: float
    dynamic_friction: float
    restitution: float

    @classmethod
    def from_array(cls, values: np.ndarray) -> "ParameterSummary":
        return cls(*(float(value) for value in values))


@dataclass(frozen=True)
class ActionObservation:
    kind: str
    values: tuple[float, ...]
    sigma: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.values) != len(self.sigma) or not self.values:
            raise ValueError("observation values and sigma must have equal non-zero length")
        if any(not np.isfinite(value) for value in self.values):
            raise ValueError("observation values must be finite")
        if any(not np.isfinite(value) or value <= 0.0 for value in self.sigma):
            raise ValueError("observation sigma must be finite and positive")


@dataclass
class PhysicalBelief:
    particles: np.ndarray
    log_weights: np.ndarray
    rng: np.random.Generator

    @classmethod
    def uniform(cls, seed: int, particles: int) -> "PhysicalBelief":
        if particles <= 0:
            raise ValueError("particle count must be positive")
        rng = np.random.default_rng(seed)
        samples = rng.uniform(PARAMETER_BOUNDS[:, 0], PARAMETER_BOUNDS[:, 1], size=(particles, 4))
        samples[:, 2] = np.minimum(samples[:, 2], samples[:, 1])
        return cls(samples, np.full(particles, -np.log(particles)), rng)

    @property
    def weights(self) -> np.ndarray:
        return np.exp(self.log_weights - logsumexp(self.log_weights))

    @property
    def mean(self) -> ParameterSummary:
        return ParameterSummary.from_array(np.average(self.particles, axis=0, weights=self.weights))

    @property
    def std(self) -> ParameterSummary:
        mean = np.asarray(tuple(self.mean.__dict__.values()))
        variance = np.average((self.particles - mean) ** 2, axis=0, weights=self.weights)
        return ParameterSummary.from_array(np.sqrt(variance))

    @property
    def effective_sample_size(self) -> float:
        weights = self.weights
        return float(1.0 / np.sum(weights * weights))

    def percentile(self, percentile: float) -> np.ndarray:
        if not 0.0 <= percentile <= 100.0:
            raise ValueError("percentile must lie in [0, 100]")
        result = []
        target = percentile / 100.0
        for column in range(self.particles.shape[1]):
            order = np.argsort(self.particles[:, column])
            cumulative = np.cumsum(self.weights[order])
            index = min(int(np.searchsorted(cumulative, target, side="left")), len(order) - 1)
            result.append(self.particles[order[index], column])
        return np.asarray(result)


def predict_measurement(particles: np.ndarray, action: Action) -> np.ndarray:
    particles = np.asarray(particles, dtype=np.float64)
    if particles.ndim != 2 or particles.shape[1] != 4:
        raise ValueError("particles must have shape (N, 4)")
    if action.kind == "vertical_accel":
        return (particles[:, 0] * (9.81 + action.magnitude))[:, None]
    if action.kind == "incline":
        onset_angle_deg = np.degrees(np.arctan(particles[:, 1]))
        return np.column_stack((onset_angle_deg, particles[:, 2]))
    if action.kind == "drop":
        return particles[:, 3, None]
    if action.kind == "passive_push":
        initial_velocity = action.magnitude / particles[:, 0]
        stop_time = initial_velocity / (9.81 * np.maximum(particles[:, 2], 1e-6))
        return np.column_stack((initial_velocity, stop_time))
    raise ValueError(f"unsupported action kind: {action.kind}")


def _copy_rng(rng: np.random.Generator) -> np.random.Generator:
    cloned = np.random.default_rng()
    cloned.bit_generator.state = copy.deepcopy(rng.bit_generator.state)
    return cloned


def update_belief(
    belief: PhysicalBelief,
    action: Action,
    observation: ActionObservation,
) -> PhysicalBelief:
    if action.kind != observation.kind:
        raise ValueError("action and observation kinds must match")
    prediction = predict_measurement(belief.particles, action)
    observed = np.asarray(observation.values, dtype=np.float64)
    sigma = np.asarray(observation.sigma, dtype=np.float64)
    if prediction.shape[1] != len(observed):
        raise ValueError("observation dimension does not match action model")
    residual = (prediction - observed[None, :]) / sigma[None, :]
    log_weights = belief.log_weights - 0.5 * np.sum(residual * residual, axis=1)
    log_weights -= logsumexp(log_weights)
    updated = PhysicalBelief(belief.particles.copy(), log_weights, _copy_rng(belief.rng))
    if updated.effective_sample_size < len(updated.particles) / 2.0:
        updated = _resample(updated)
    return updated


def _resample(belief: PhysicalBelief) -> PhysicalBelief:
    count = len(belief.particles)
    positions = (belief.rng.random() + np.arange(count)) / count
    indices = np.searchsorted(np.cumsum(belief.weights), positions, side="right")
    particles = belief.particles[np.minimum(indices, count - 1)].copy()
    jitter = (PARAMETER_BOUNDS[:, 1] - PARAMETER_BOUNDS[:, 0]) * 0.003
    particles += belief.rng.normal(0.0, jitter, size=particles.shape)
    particles = np.clip(particles, PARAMETER_BOUNDS[:, 0], PARAMETER_BOUNDS[:, 1])
    particles[:, 2] = np.minimum(particles[:, 2], particles[:, 1])
    return PhysicalBelief(particles, np.full(count, -np.log(count)), belief.rng)


_MATERIAL_MODELS = {
    "wood": np.asarray([0.95, 0.58, 0.42, 0.25]),
    "plastic": np.asarray([0.65, 0.38, 0.28, 0.52]),
    "metal": np.asarray([1.45, 0.30, 0.22, 0.38]),
    "rubber": np.asarray([0.55, 0.78, 0.65, 0.70]),
}


def material_prior(
    class_probabilities: dict[str, float],
    seed: int,
    particles: int,
) -> PhysicalBelief:
    if particles <= 0:
        raise ValueError("particle count must be positive")
    unknown = set(class_probabilities).difference(_MATERIAL_MODELS)
    if unknown:
        raise ValueError(f"unknown material classes: {sorted(unknown)}")
    labels = tuple(class_probabilities)
    probabilities = np.asarray([class_probabilities[label] for label in labels], dtype=np.float64)
    if np.any(probabilities < 0.0) or probabilities.sum() <= 0.0:
        raise ValueError("material probabilities must be non-negative and non-zero")
    probabilities /= probabilities.sum()
    rng = np.random.default_rng(seed)
    chosen = rng.choice(len(labels), size=particles, p=probabilities)
    widths = PARAMETER_BOUNDS[:, 1] - PARAMETER_BOUNDS[:, 0]
    samples = np.empty((particles, 4), dtype=np.float64)
    for index, label in enumerate(labels):
        selected = chosen == index
        samples[selected] = rng.normal(_MATERIAL_MODELS[label], widths * 0.16, size=(selected.sum(), 4))
    samples = np.clip(samples, PARAMETER_BOUNDS[:, 0], PARAMETER_BOUNDS[:, 1])
    samples[:, 2] = np.minimum(samples[:, 2], samples[:, 1])
    return PhysicalBelief(samples, np.full(particles, -np.log(particles)), rng)
