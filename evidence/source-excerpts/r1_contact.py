"""Validation contract for the R1 Pro contact-replication stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


def point_cloud_to_aabbs_gap(points_world: np.ndarray, aabbs_world: np.ndarray) -> float:
    """Return the minimum Euclidean gap from reconstructed surface points to boxes."""

    points = np.asarray(points_world, dtype=np.float64)
    boxes = np.asarray(aabbs_world, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) == 0:
        raise ValueError("surface points must have shape (N, 3), N >= 1")
    if boxes.ndim != 3 or boxes.shape[1:] != (2, 3) or len(boxes) == 0:
        raise ValueError("AABBs must have shape (B, 2, 3), B >= 1")
    if not np.all(np.isfinite(points)) or not np.all(np.isfinite(boxes)):
        raise ValueError("surface points and AABBs must be finite")
    if np.any(boxes[:, 1] < boxes[:, 0]):
        raise ValueError("each AABB maximum must be >= its minimum")
    below = np.maximum(boxes[None, :, 0, :] - points[:, None, :], 0.0)
    above = np.maximum(points[:, None, :] - boxes[None, :, 1, :], 0.0)
    distances = np.linalg.norm(below + above, axis=-1)
    return float(distances.min())


@dataclass(frozen=True)
class ContactRunSummary:
    success: bool
    first_contact_step: int | None
    contact_step_count: int
    object_displacement_m: float
    eef_path_length_m: float
    failure_reason: str | None


@dataclass(frozen=True)
class ContactValidation:
    success: bool
    failure_reasons: tuple[str, ...]
    first_finger_contact_step: int | None
    first_object_motion_step: int | None
    visible_gap_at_contact_m: float | None
    maximum_object_speed_m_s: float
    maximum_eef_speed_m_s: float
    maximum_eef_transverse_step_m: float


def validate_contact_run(
    object_positions: np.ndarray,
    eef_positions: np.ndarray,
    contact_pairs_by_step: dict[str, list[list[str]]],
    visible_surface_gaps_m: np.ndarray,
    frame_dt_s: float,
    *,
    allowed_finger_link_token: str = "right_gripper_finger_link",
    motion_tolerance_m: float = 0.003,
    visible_contact_tolerance_m: float = 0.008,
    maximum_object_speed_m_s: float = 0.50,
    maximum_eef_speed_m_s: float = 0.50,
    maximum_eef_transverse_step_m: float = 0.005,
    minimum_post_contact_motion_m: float = 0.005,
) -> ContactValidation:
    """Fail closed unless a smooth, visible finger contact explains object motion.

    This is intentionally stricter than :func:`summarize_contact_run`.  A PhysX
    contact flag alone is not evidence when a hidden wrist/sensor link collided,
    when the rendered GS is visibly separated from the fingers, or when a large
    depenetration impulse ejects the object.
    """

    object_values = np.asarray(object_positions, dtype=np.float64)
    eef_values = np.asarray(eef_positions, dtype=np.float64)
    gaps = np.asarray(visible_surface_gaps_m, dtype=np.float64)
    if (
        object_values.ndim != 2
        or eef_values.ndim != 2
        or object_values.shape != eef_values.shape
        or object_values.shape[1] != 3
        or len(object_values) < 2
    ):
        raise ValueError("object and EEF trajectories must share shape (T, 3), T >= 2")
    if gaps.shape != (len(object_values),):
        raise ValueError("visible surface gaps must have shape (T,)")
    if frame_dt_s <= 0.0 or not np.isfinite(frame_dt_s):
        raise ValueError("frame_dt_s must be finite and positive")
    if not np.all(np.isfinite(object_values)) or not np.all(np.isfinite(eef_values)) or not np.all(np.isfinite(gaps)):
        raise ValueError("contact validation inputs must be finite")

    finger_contact_steps: list[int] = []
    non_finger_contact = False
    for step_text, pairs in contact_pairs_by_step.items():
        step = int(step_text)
        if step < 0 or step >= len(object_values):
            raise ValueError("contact step lies outside the trajectory")
        for pair in pairs:
            if len(pair) != 2:
                raise ValueError("each contact pair must contain exactly two prim paths")
            robot_path = pair[1]
            if allowed_finger_link_token in robot_path:
                finger_contact_steps.append(step)
            else:
                non_finger_contact = True

    first_finger_contact = min(finger_contact_steps) if finger_contact_steps else None
    initial_object = object_values[0]
    displacement_from_start = np.linalg.norm(object_values - initial_object, axis=1)
    moving = np.flatnonzero(displacement_from_start > motion_tolerance_m)
    first_motion = int(moving[0]) if len(moving) else None

    object_steps = np.linalg.norm(np.diff(object_values, axis=0), axis=1)
    eef_deltas = np.diff(eef_values, axis=0)
    eef_steps = np.linalg.norm(eef_deltas, axis=1)
    max_object_speed = float(object_steps.max(initial=0.0) / frame_dt_s)
    max_eef_speed = float(eef_steps.max(initial=0.0) / frame_dt_s)

    net_eef_motion = eef_values[-1] - eef_values[0]
    net_norm = float(np.linalg.norm(net_eef_motion))
    if net_norm > 1e-12:
        approach_axis = net_eef_motion / net_norm
        axial = eef_deltas @ approach_axis
        transverse = eef_deltas - axial[:, None] * approach_axis[None, :]
        max_transverse_step = float(np.linalg.norm(transverse, axis=1).max(initial=0.0))
    else:
        max_transverse_step = float(eef_steps.max(initial=0.0))

    reasons: list[str] = []
    if first_finger_contact is None:
        reasons.append("no_finger_contact")
    if non_finger_contact:
        reasons.append("non_finger_robot_contact")
    if first_motion is not None and (first_finger_contact is None or first_motion < first_finger_contact):
        reasons.append("object_moved_before_finger_contact")
    visible_gap = None if first_finger_contact is None else float(gaps[first_finger_contact])
    if visible_gap is not None and visible_gap > visible_contact_tolerance_m:
        reasons.append("visible_surface_not_in_contact")
    if max_object_speed > maximum_object_speed_m_s:
        reasons.append("object_speed_exceeds_limit")
    if max_eef_speed > maximum_eef_speed_m_s:
        reasons.append("eef_speed_exceeds_limit")
    if max_transverse_step > maximum_eef_transverse_step_m:
        reasons.append("eef_transverse_jitter_exceeds_limit")
    if first_finger_contact is not None:
        post_contact_motion = float(
            np.linalg.norm(object_values[-1] - object_values[first_finger_contact])
        )
        if post_contact_motion < minimum_post_contact_motion_m:
            reasons.append("finger_contact_without_object_motion")

    return ContactValidation(
        success=not reasons,
        failure_reasons=tuple(reasons),
        first_finger_contact_step=first_finger_contact,
        first_object_motion_step=first_motion,
        visible_gap_at_contact_m=visible_gap,
        maximum_object_speed_m_s=max_object_speed,
        maximum_eef_speed_m_s=max_eef_speed,
        maximum_eef_transverse_step_m=max_transverse_step,
    )


def summarize_contact_run(
    object_positions: np.ndarray,
    eef_positions: np.ndarray,
    contact_steps: Iterable[int],
    minimum_displacement_m: float = 0.02,
) -> ContactRunSummary:
    object_values = np.asarray(object_positions, dtype=np.float64)
    eef_values = np.asarray(eef_positions, dtype=np.float64)
    if (
        object_values.ndim != 2
        or eef_values.ndim != 2
        or object_values.shape != eef_values.shape
        or object_values.shape[1] != 3
        or len(object_values) < 2
    ):
        raise ValueError("object and EEF trajectories must share shape (T, 3), T >= 2")
    if not np.all(np.isfinite(object_values)) or not np.all(np.isfinite(eef_values)):
        raise ValueError("contact trajectories must be finite")
    steps = tuple(sorted({int(step) for step in contact_steps}))
    if any(step < 0 or step >= len(object_values) for step in steps):
        raise ValueError("contact step lies outside the trajectory")
    displacement = float(np.linalg.norm(object_values[-1] - object_values[0]))
    path_length = float(np.sum(np.linalg.norm(np.diff(eef_values, axis=0), axis=1)))
    if not steps:
        failure_reason = "no_r1_object_contact_detected"
    elif displacement < minimum_displacement_m:
        failure_reason = "contact_without_sufficient_object_motion"
    else:
        failure_reason = None
    return ContactRunSummary(
        success=failure_reason is None,
        first_contact_step=steps[0] if steps else None,
        contact_step_count=len(steps),
        object_displacement_m=displacement,
        eef_path_length_m=path_length,
        failure_reason=failure_reason,
    )
