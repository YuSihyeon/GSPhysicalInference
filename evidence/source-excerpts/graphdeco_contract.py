"""Validation for the immutable Graphdeco training contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PINNED_GRAPHDECO_REVISION = "54c035f7834b564019656c3e3fcc3646292f727d"


def _resolved(path_value: str, *, config_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    project_root = config_path.parent.parent
    return (project_root / path).resolve()


def _require_value(payload: dict[str, Any], field: str, expected: Any, message: str) -> None:
    if payload.get(field) != expected:
        raise ValueError(message)


def validate_training_contract(config_path: str | Path) -> dict[str, Any]:
    """Validate the canonical 7k training contract and return normalized values."""

    config_path = Path(config_path).resolve()
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    _require_value(
        payload,
        "graphdeco_revision",
        PINNED_GRAPHDECO_REVISION,
        "training requires the pinned Graphdeco revision",
    )
    _require_value(payload, "iterations", 7000, "canonical run requires 7,000 iterations")
    _require_value(payload, "resolution", 1, "canonical resolution must be 1")
    _require_value(payload, "data_device", "cpu", "canonical run requires CPU image storage")
    _require_value(payload, "white_background", True, "canonical run requires a white background")
    _require_value(payload, "train_view_count", 480, "contract requires 480 training views")
    _require_value(payload, "validation_view_count", 60, "contract requires 60 validation views")
    _require_value(payload, "test_view_count", 60, "contract requires 60 test views")

    path_fields = (
        "prepared_dataset",
        "source_manifest",
        "split_manifest",
        "image_manifest",
        "initialization_ply",
        "output_directory",
        "optimized_ply",
    )
    normalized = dict(payload)
    for field in path_fields:
        if field not in payload:
            raise ValueError(f"contract is missing {field}")
        normalized[field] = str(_resolved(payload[field], config_path=config_path))

    for field in ("prepared_dataset", "source_manifest", "split_manifest", "image_manifest", "initialization_ply"):
        if not Path(normalized[field]).exists():
            raise FileNotFoundError(f"{field} does not exist: {normalized[field]}")

    initialization = Path(normalized["initialization_ply"])
    optimized = Path(normalized["optimized_ply"])
    output_directory = Path(normalized["output_directory"])
    expected_suffix = Path("point_cloud") / "iteration_7000" / "point_cloud.ply"
    try:
        relative_output = optimized.relative_to(output_directory)
    except ValueError as error:
        raise ValueError("optimized Graphdeco output must be beneath output_directory") from error
    if relative_output != expected_suffix or optimized == initialization:
        raise ValueError(
            "optimized Graphdeco output must be point_cloud/iteration_7000/point_cloud.ply, not initialization"
        )

    normalized["command_arguments"] = [
        "--iterations",
        "7000",
        "--save_iterations",
        "100",
        "7000",
        "--test_iterations",
        "7000",
        "--checkpoint_iterations",
        "1000",
        "7000",
        "--white_background",
        "--data_device",
        "cpu",
        "-r",
        "1",
        "--disable_viewer",
    ]
    return normalized
