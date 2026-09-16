"""Calibrated multiview observation contract for GS reconstruction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class CameraFrame:
    view_id: int
    rgb_path: Path
    depth_path: Path
    mask_path: Path
    intrinsics: np.ndarray
    camera_to_world: np.ndarray


@dataclass(frozen=True)
class ObservationDataset:
    root: Path
    scene_id: str
    asset_ids: tuple[str, ...]
    width: int
    height: int
    frames: tuple[CameraFrame, ...]

    @classmethod
    def validate(cls, root: str | Path) -> "ObservationDataset":
        root = Path(root)
        payload = json.loads((root / "transforms.json").read_text(encoding="utf-8"))
        raw_frames = payload["frames"]
        if len(raw_frames) != 48:
            raise ValueError(f"expected 48 calibrated views, found {len(raw_frames)}")

        width = int(payload["width"])
        height = int(payload["height"])
        frames: list[CameraFrame] = []
        for index, raw in enumerate(raw_frames):
            if raw["view_id"] != index:
                raise ValueError("view IDs must be unique and sequential")
            intrinsics = np.asarray(raw["intrinsics"], dtype=np.float64)
            pose = np.asarray(raw["camera_to_world"], dtype=np.float64)
            if intrinsics.shape != (3, 3) or abs(np.linalg.det(intrinsics)) < 1e-12:
                raise ValueError("camera intrinsics must be invertible 3x3 matrices")
            if pose.shape != (4, 4) or not np.all(np.isfinite(pose)):
                raise ValueError("camera-to-world pose must be a finite 4x4 matrix")
            rotation = pose[:3, :3]
            if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6):
                raise ValueError("camera rotation must be orthonormal")
            if not np.allclose(pose[3], [0.0, 0.0, 0.0, 1.0], atol=1e-9):
                raise ValueError("camera pose must use homogeneous coordinates")

            rgb_path = root / raw["rgb_path"]
            depth_path = root / raw["depth_path"]
            mask_path = root / raw["mask_path"]
            for path in (rgb_path, depth_path, mask_path):
                if not path.is_file():
                    raise ValueError(f"missing observation file: {path}")
            rgb = np.load(rgb_path)
            depth = np.load(depth_path)
            mask = np.load(mask_path)
            if rgb.shape != (height, width, 3):
                raise ValueError("RGB shape does not match dataset dimensions")
            if depth.shape != (height, width) or not np.all(np.isfinite(depth)):
                raise ValueError("depth must be finite and match dataset dimensions")
            if np.any(depth < 0.0):
                raise ValueError("depth must be non-negative")
            if mask.shape != (height, width):
                raise ValueError("instance mask shape does not match dataset dimensions")
            frames.append(
                CameraFrame(
                    view_id=index,
                    rgb_path=rgb_path,
                    depth_path=depth_path,
                    mask_path=mask_path,
                    intrinsics=intrinsics,
                    camera_to_world=pose,
                )
            )

        return cls(
            root=root,
            scene_id=str(payload["scene_id"]),
            asset_ids=tuple(str(value) for value in payload["asset_ids"]),
            width=width,
            height=height,
            frames=tuple(frames),
        )


def _look_at_pose(position: np.ndarray, target: np.ndarray) -> np.ndarray:
    forward = target - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    rotation = np.column_stack((right, up, -forward))
    pose = np.eye(4, dtype=np.float64)
    pose[:3, :3] = rotation
    pose[:3, 3] = position
    return pose


def generate_camera_ring(
    count: int,
    radius_m: float = 1.2,
    target_height_m: float = 0.12,
) -> np.ndarray:
    if count <= 0:
        raise ValueError("camera count must be positive")
    heights = (0.35, 0.65, 0.95)
    poses = []
    for index in range(count):
        band = min((index * 3) // count, 2)
        band_start = (band * count + 2) // 3
        band_end = ((band + 1) * count + 2) // 3
        band_size = max(band_end - band_start, 1)
        within_band = index - band_start
        angle = 2.0 * np.pi * within_band / band_size + band * 0.13
        position = np.array(
            [radius_m * np.cos(angle), radius_m * np.sin(angle), heights[band]],
            dtype=np.float64,
        )
        poses.append(_look_at_pose(position, np.array([0.0, 0.0, target_height_m])))
    return np.stack(poses)

