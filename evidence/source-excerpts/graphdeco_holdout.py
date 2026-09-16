"""Held-out camera isolation helpers for Graphdeco rendering."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np


def foreground_bounding_box(
    rgb: np.ndarray,
    *,
    threshold: int = 250,
    padding_fraction: float = 0.25,
) -> tuple[int, int, int, int]:
    """Return a padded PIL-style crop box around non-white reference pixels."""

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("rgb must have shape (height, width, 3)")
    if padding_fraction < 0:
        raise ValueError("padding_fraction must be non-negative")
    height, width, _ = rgb.shape
    foreground = np.any(rgb < threshold, axis=2)
    ys, xs = np.nonzero(foreground)
    if len(xs) == 0:
        return (0, 0, width, height)

    left = int(xs.min())
    right = int(xs.max()) + 1
    top = int(ys.min())
    bottom = int(ys.max()) + 1
    pad = int(round(max(right - left, bottom - top) * padding_fraction))
    return (
        max(0, left - pad),
        max(0, top - pad),
        min(width, right + pad),
        min(height, bottom + pad),
    )


def order_holdout_video_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order held-out views into reproducible, camera-wise rotation sequences."""

    split_order = {"validation": 0, "test": 1}
    return sorted(
        rows,
        key=lambda row: (
            split_order.get(str(row["split"]), 99),
            int(row["camera_id"]),
            int(row["angle"]),
        ),
    )


def _training_image_names(images_txt: Path) -> set[str]:
    names: set[str] = set()
    for line in images_txt.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens = stripped.split()
        if len(tokens) >= 10:
            names.add(tokens[9])
    return names


def load_holdout_records(
    prepared_root: str | Path, split: str
) -> list[dict[str, Any]]:
    """Load validation/test cameras and prove that none were training inputs."""

    if split not in {"validation", "test"}:
        raise ValueError("split must be validation or test")
    prepared_root = Path(prepared_root).resolve()
    training_names = _training_image_names(prepared_root / "sparse" / "0" / "images.txt")
    records = json.loads(
        (prepared_root / f"{split}_views.json").read_text(encoding="utf-8")
    )
    normalized: list[dict[str, Any]] = []
    expected_prefix = ("evaluation", split, "images")
    for raw in records:
        relative = PurePosixPath(raw["image_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe held-out image path: {relative}")
        if relative.parts[:3] != expected_prefix:
            raise ValueError(
                f"{split} image must be beneath evaluation/{split}/images: {relative}"
            )
        image_name = relative.name
        if image_name in training_names:
            raise ValueError(f"held-out image leaks into training: {image_name}")
        reference_path = prepared_root.joinpath(*relative.parts)
        if not reference_path.is_file():
            raise FileNotFoundError(f"held-out reference does not exist: {reference_path}")

        intrinsic = np.asarray(raw["intrinsic"], dtype=float)
        camera_from_world = np.asarray(raw["camera_from_world"], dtype=float)
        if intrinsic.shape != (3, 3):
            raise ValueError(f"invalid intrinsic shape for {image_name}: {intrinsic.shape}")
        if camera_from_world.shape != (4, 4):
            raise ValueError(
                f"invalid camera_from_world shape for {image_name}: {camera_from_world.shape}"
            )
        if int(raw["width"]) <= 0 or int(raw["height"]) <= 0:
            raise ValueError(f"invalid image dimensions for {image_name}")

        record = dict(raw)
        record.update(
            {
                "split": split,
                "image_name": image_name,
                "reference_path": str(reference_path),
            }
        )
        normalized.append(record)
    return normalized


def validate_optimized_model_path(
    optimized_ply: str | Path, expected_iteration: int
) -> Path:
    optimized_ply = Path(optimized_ply).resolve()
    expected_directory = f"iteration_{expected_iteration}"
    if (
        optimized_ply.name != "point_cloud.ply"
        or optimized_ply.parent.name != expected_directory
        or optimized_ply.parent.parent.name != "point_cloud"
    ):
        raise ValueError(
            f"model must be point_cloud/{expected_directory}/point_cloud.ply"
        )
    if not optimized_ply.is_file():
        raise FileNotFoundError(f"optimized model does not exist: {optimized_ply}")
    return optimized_ply
