"""Posterior-directed active physical experiment selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

from .actions import Action, candidate_actions
from .belief import PhysicalBelief, predict_measurement
from .decision_trace import DecisionTrace


_MEASUREMENT_SIGMA = {
    "vertical_accel": np.asarray([0.10]),
    "incline": np.asarray([0.70, 0.03]),
    "drop": np.asarray([0.02]),
}


@dataclass(frozen=True)
class CandidateScore:
    action: Action
    information_score: float
    cost_penalty: float
    safety_penalty: float
    total_score: float


@dataclass(frozen=True)
class SelectionResult:
    action: Action
    scores: tuple[CandidateScore, ...]
    posterior: PhysicalBelief

    def to_trace(self, step: int) -> DecisionTrace:
        names = ("mass", "static_friction", "dynamic_friction", "restitution")
        mean = tuple(self.posterior.mean.__dict__.values())
        low = self.posterior.percentile(5)
        high = self.posterior.percentile(95)
        posterior_summary = {
            name: {"mean": float(mean[index]), "p05": float(low[index]), "p95": float(high[index])}
            for index, name in enumerate(names)
        }
        score_payload = tuple(
            {
                "action": asdict(score.action),
                "information_score": score.information_score,
                "cost_penalty": score.cost_penalty,
                "safety_penalty": score.safety_penalty,
                "total_score": score.total_score,
            }
            for score in self.scores
        )
        winner = next(score for score in self.scores if score.action == self.action)
        reason = (
            f"selected maximum score {winner.total_score:.6f}: "
            f"information {winner.information_score:.6f} - "
            f"cost {winner.cost_penalty:.6f} - safety {winner.safety_penalty:.6f}"
        )
        return DecisionTrace(
            step=step,
            posterior_summary=posterior_summary,
            candidate_scores=score_payload,
            selected_action=asdict(self.action),
            reason=reason,
        )


def _stratified_particles(belief: PhysicalBelief, maximum: int = 512) -> np.ndarray:
    count = min(maximum, len(belief.particles))
    quantiles = (np.arange(count, dtype=np.float64) + 0.5) / count
    indices = np.searchsorted(np.cumsum(belief.weights), quantiles, side="left")
    return belief.particles[np.minimum(indices, len(belief.particles) - 1)]


def score_candidate(belief: PhysicalBelief, action: Action) -> CandidateScore:
    prediction = predict_measurement(_stratified_particles(belief), action)
    variance = np.var(prediction, axis=0)
    sigma = _MEASUREMENT_SIGMA[action.kind]
    information = float(np.sum(np.log1p(variance / (sigma * sigma))))
    cost_penalty = 0.05 * action.cost
    if action.kind == "vertical_accel":
        safety_penalty = 0.015 * (action.magnitude / 1.5) ** 2
    elif action.kind == "drop":
        safety_penalty = 0.02 * (action.magnitude / 0.45) ** 2
    else:
        safety_penalty = 0.01 * (action.magnitude / 6.0) ** 2
    return CandidateScore(
        action=action,
        information_score=information,
        cost_penalty=cost_penalty,
        safety_penalty=safety_penalty,
        total_score=information - cost_penalty - safety_penalty,
    )


def select_action(
    belief: PhysicalBelief,
    used: Sequence[Action],
) -> SelectionResult:
    used_set = set(used)
    available = [action for action in candidate_actions() if action not in used_set]
    if not available:
        raise ValueError("all candidate actions have been used")
    scores = tuple(score_candidate(belief, action) for action in available)
    winner = max(scores, key=lambda score: score.total_score)
    return SelectionResult(winner.action, scores, belief)

