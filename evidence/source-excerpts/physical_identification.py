"""Observable-to-parameter estimators for the three rigid-body probes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ScalarEstimate:
    value: float
    residual: float
    observable: str


def estimate_mass_from_contact_impulse(
    contact_impulses_ns: np.ndarray,
    velocity_before_m_s: tuple[float, float, float],
    velocity_after_m_s: tuple[float, float, float],
) -> ScalarEstimate:
    """Estimate mass from linear momentum: sum(J) = m * delta(v)."""

    impulses = np.asarray(contact_impulses_ns, dtype=np.float64)
    if impulses.ndim != 2 or impulses.shape[1] != 3 or not np.all(np.isfinite(impulses)):
        raise ValueError("contact impulses must have finite shape (N, 3)")
    delta_v = np.asarray(velocity_after_m_s, dtype=np.float64) - np.asarray(
        velocity_before_m_s, dtype=np.float64
    )
    if delta_v.shape != (3,) or not np.all(np.isfinite(delta_v)) or np.linalg.norm(delta_v) < 1e-6:
        raise ValueError("velocity change must be a finite non-zero vector")
    total_impulse = impulses.sum(axis=0)
    mass = float(np.dot(total_impulse, delta_v) / np.dot(delta_v, delta_v))
    if mass <= 0.0:
        raise ValueError("contact impulse and velocity change imply non-positive mass")
    residual = float(np.linalg.norm(total_impulse - mass * delta_v))
    return ScalarEstimate(mass, residual, "robot_contact_impulse_over_velocity_change")


def estimate_static_friction(slip_onset_angle_deg: float) -> ScalarEstimate:
    angle = float(slip_onset_angle_deg)
    if not np.isfinite(angle) or not 0.0 <= angle < 89.0:
        raise ValueError("slip onset angle must lie in [0, 89) degrees")
    return ScalarEstimate(float(np.tan(np.deg2rad(angle))), 0.0, "incline_slip_onset")


def estimate_dynamic_friction(
    angle_deg: float, downhill_acceleration_m_s2: float, gravity_m_s2: float = 9.81
) -> ScalarEstimate:
    angle = float(angle_deg)
    acceleration = float(downhill_acceleration_m_s2)
    if not all(np.isfinite(value) for value in (angle, acceleration, gravity_m_s2)):
        raise ValueError("incline inputs must be finite")
    if not 0.0 < angle < 89.0 or gravity_m_s2 <= 0.0:
        raise ValueError("incline angle and gravity must be positive")
    radians = np.deg2rad(angle)
    value = float(
        (gravity_m_s2 * np.sin(radians) - acceleration)
        / (gravity_m_s2 * np.cos(radians))
    )
    if value < 0.0:
        raise ValueError("observed acceleration implies negative dynamic friction")
    return ScalarEstimate(value, 0.0, "fixed_incline_downhill_acceleration")


def estimate_restitution(
    pre_impact_normal_speed_m_s: float, post_impact_normal_speed_m_s: float
) -> ScalarEstimate:
    before = float(pre_impact_normal_speed_m_s)
    after = float(post_impact_normal_speed_m_s)
    if not np.isfinite(before) or not np.isfinite(after):
        raise ValueError("impact speeds must be finite")
    if before >= 0.0:
        raise ValueError("pre-impact normal velocity must be approaching the surface")
    if after < 0.0:
        raise ValueError("post-impact normal velocity must leave the surface")
    return ScalarEstimate(float(after / -before), 0.0, "drop_impact_velocity_ratio")

