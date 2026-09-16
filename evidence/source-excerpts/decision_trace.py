"""Auditable, numerical decision traces for the embodied agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionTrace:
    step: int
    posterior_summary: dict[str, dict[str, float]]
    candidate_scores: tuple[dict[str, Any], ...]
    selected_action: dict[str, Any]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

