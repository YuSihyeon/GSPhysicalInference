"""Robot-executable physical identification actions."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal


ActionKind = Literal["passive_push", "vertical_accel", "incline", "drop"]


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    magnitude: float
    duration_s: float
    cost: float
    precondition: str

    def __post_init__(self) -> None:
        if self.kind not in {"passive_push", "vertical_accel", "incline", "drop"}:
            raise ValueError(f"unknown action kind: {self.kind}")
        if not math.isfinite(self.magnitude) or self.magnitude < 0.0:
            raise ValueError("action magnitude must be finite and non-negative")
        if not math.isfinite(self.duration_s) or self.duration_s <= 0.0:
            raise ValueError("action duration must be finite and positive")
        if not math.isfinite(self.cost) or self.cost < 0.0:
            raise ValueError("action cost must be finite and non-negative")
        if not self.precondition:
            raise ValueError("action precondition must be non-empty")


def candidate_actions() -> tuple[Action, ...]:
    return (
        Action("vertical_accel", 0.3, 1.5, 1.2, "grasped"),
        Action("vertical_accel", 0.8, 1.5, 1.4, "grasped"),
        Action("vertical_accel", 1.5, 1.5, 1.8, "grasped"),
        Action("incline", 2.0, 12.0, 1.0, "on_board"),
        Action("incline", 6.0, 5.0, 1.1, "on_board"),
        Action("drop", 0.10, 2.0, 0.8, "held_above_board"),
        Action("drop", 0.25, 2.0, 1.0, "held_above_board"),
        Action("drop", 0.45, 2.0, 1.3, "held_above_board"),
    )


def fixed_schedule() -> tuple[Action, Action, Action]:
    by_key = {(action.kind, action.magnitude): action for action in candidate_actions()}
    return (
        by_key[("vertical_accel", 0.8)],
        by_key[("incline", 2.0)],
        by_key[("drop", 0.25)],
    )


def passive_push_action() -> Action:
    return Action("passive_push", 0.45, 2.0, 0.0, "on_board")
