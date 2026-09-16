"""Freeze a public prior + motion + active estimate without opening private GT."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gs_embodied_twin.estimate_fusion import fuse_scalar, validate_measurement


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physion-jsonl", type=Path, required=True)
    parser.add_argument("--geometry-manifest", type=Path, required=True)
    parser.add_argument("--motion-result", type=Path, required=True)
    parser.add_argument("--active-mass-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    geometry = json.loads(args.geometry_manifest.read_text(encoding="utf-8"))
    motion = json.loads(args.motion_result.read_text(encoding="utf-8"))
    active = json.loads(args.active_mass_result.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in args.physion_jsonl.read_text(encoding="utf-8").splitlines()]

    empirical = {
        key: float(statistics.median(float(row[key]) for row in rows))
        for key in ("mass_kg", "static_friction", "dynamic_friction", "restitution")
    }
    volume = float(geometry["collider"]["volume_m3"])
    semantic_mass = volume * 1050.0
    prior = {
        "mass_kg": 0.5 * semantic_mass + 0.5 * empirical["mass_kg"],
        "static_friction": 0.5 * 0.30 + 0.5 * empirical["static_friction"],
        "dynamic_friction": 0.5 * 0.25 + 0.5 * empirical["dynamic_friction"],
        "restitution": 0.5 * 0.10 + 0.5 * empirical["restitution"],
    }

    dynamic_observation = float(motion["probes"]["dynamic_friction"]["estimate"])
    restitution_observation = float(motion["probes"]["restitution"]["estimate"])
    static_observation = float(motion["probes"]["static_friction"]["estimate"])
    mass_measurement = active.get("mass_identification")
    mass_valid = bool(
        mass_measurement
        and validate_measurement(
            status=active.get("status", ""),
            residual=float(mass_measurement["momentum_residual_ns"]),
            residual_limit=0.05,
        )
    )

    posterior = {
        "mass_kg": (
            fuse_scalar(
                prior_value=prior["mass_kg"],
                measurement_value=float(mass_measurement["estimate_kg"]),
                measurement_weight=0.85,
            )
            if mass_valid
            else prior["mass_kg"]
        ),
        "static_friction": fuse_scalar(
            prior_value=prior["static_friction"],
            measurement_value=static_observation,
            measurement_weight=0.35,
        ),
        "dynamic_friction": fuse_scalar(
            prior_value=prior["dynamic_friction"],
            measurement_value=dynamic_observation,
            measurement_weight=0.95,
        ),
        "restitution": fuse_scalar(
            prior_value=prior["restitution"],
            measurement_value=restitution_observation,
            measurement_weight=0.85,
        ),
    }
    result = {
        "schema_version": 1,
        "status": "frozen_before_gt_evaluation",
        "object_semantic": "006_mustard_bottle",
        "geometry_parent_sha256": geometry["geometry_parent"]["sha256"],
        "method": "semantic_material_prior_plus_action_generated_motion_plus_validated_active_measurements",
        "prior": {
            "values": prior,
            "semantic_material_hypothesis": {
                "description": "plastic container with uncertain fill; deliberately weak engineering prior",
                "equivalent_density_center_kg_m3": 1050.0,
                "gs_collider_volume_m3": volume,
                "mass_center_kg": semantic_mass,
                "warning": "heuristic prior, not ground truth",
            },
            "physion_empirical_medians": empirical,
            "physion_rows": len(rows),
        },
        "motion_observations": {
            "static_friction": {"value": static_observation, "weight": 0.35, "quality": "low; onset sensitive to contact initialization"},
            "dynamic_friction": {"value": dynamic_observation, "weight": 0.95, "quality": "high; fit restricted to on-board samples"},
            "restitution": {"value": restitution_observation, "weight": 0.85, "quality": "medium; discrete impact and collider dependent"},
        },
        "active_mass_measurement": {
            "accepted": mass_valid,
            "value_kg": None if not mass_measurement else mass_measurement["estimate_kg"],
            "momentum_residual_ns": None if not mass_measurement else mass_measurement["momentum_residual_ns"],
            "rejection_rule": "status must be completed and momentum residual <= 0.05 N s",
        },
        "posterior": posterior,
        "uncertainty": {
            "mass_kg_90pct": [0.35, 3.8],
            "static_friction_90pct": [0.12, 0.48],
            "dynamic_friction_90pct": [max(0.0, posterior["dynamic_friction"] - 0.03), posterior["dynamic_friction"] + 0.03],
            "restitution_90pct": [max(0.0, posterior["restitution"] - 0.04), posterior["restitution"] + 0.04],
        },
        "input_commitments": {
            "physion_jsonl_sha256": sha256_file(args.physion_jsonl),
            "geometry_manifest_sha256": sha256_file(args.geometry_manifest),
            "motion_result_sha256": sha256_file(args.motion_result),
            "active_mass_result_sha256": sha256_file(args.active_mass_result),
        },
        "gt_fields_read": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
