"""Build a collision proxy directly from an optimized Graphdeco Gaussian cloud."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData
from scipy.spatial.transform import Rotation
from skimage import measure
import trimesh


@dataclass(frozen=True)
class GaussianCloud:
    centers_m: np.ndarray
    opacity: np.ndarray
    scales_m: np.ndarray
    quaternions_wxyz: np.ndarray

    def __post_init__(self) -> None:
        centers = np.asarray(self.centers_m, dtype=np.float64)
        opacity = np.asarray(self.opacity, dtype=np.float64)
        scales = np.asarray(self.scales_m, dtype=np.float64)
        rotations = np.asarray(self.quaternions_wxyz, dtype=np.float64)
        count = len(centers)
        if centers.shape != (count, 3) or scales.shape != (count, 3):
            raise ValueError("centers and scales must have shape (N, 3)")
        if opacity.shape != (count,) or rotations.shape != (count, 4):
            raise ValueError("opacity and rotations must align with centers")
        if count == 0 or not all(
            np.all(np.isfinite(value)) for value in (centers, opacity, scales, rotations)
        ):
            raise ValueError("Gaussian arrays must be non-empty and finite")
        if np.any((opacity <= 0.0) | (opacity >= 1.0)) or np.any(scales <= 0.0):
            raise ValueError("activated opacity and scales must be positive and bounded")
        norms = np.linalg.norm(rotations, axis=1)
        if np.any(norms < 1e-8):
            raise ValueError("Gaussian rotations must be non-zero quaternions")


@dataclass(frozen=True)
class OccupancyField:
    values: np.ndarray
    origin_m: np.ndarray
    voxel_size_m: float
    retained_gaussian_count: int
    total_gaussian_count: int


@dataclass(frozen=True)
class DensityColliderResult:
    occupancy: OccupancyField
    surface_mesh: trimesh.Trimesh
    convex_collider: trimesh.Trimesh


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sigmoid(values: np.ndarray) -> np.ndarray:
    positive = values >= 0
    result = np.empty_like(values, dtype=np.float64)
    result[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exponential = np.exp(values[~positive])
    result[~positive] = exponential / (1.0 + exponential)
    return result


def load_graphdeco_gaussians(path: str | Path) -> GaussianCloud:
    """Load and activate the geometry fields in an optimized Graphdeco PLY."""

    path = Path(path).resolve()
    if path.name != "point_cloud.ply" or not path.is_file():
        raise ValueError("optimized Graphdeco input must be an existing point_cloud.ply")
    vertex = PlyData.read(path)["vertex"].data
    required = {
        "x", "y", "z", "opacity",
        "scale_0", "scale_1", "scale_2",
        "rot_0", "rot_1", "rot_2", "rot_3",
    }
    missing = required.difference(vertex.dtype.names or ())
    if missing:
        raise ValueError(f"optimized PLY is missing Gaussian fields: {sorted(missing)}")
    centers = np.column_stack([vertex[name] for name in ("x", "y", "z")]).astype(np.float64)
    opacity = _sigmoid(np.asarray(vertex["opacity"], dtype=np.float64))
    scales = np.exp(
        np.column_stack([vertex[name] for name in ("scale_0", "scale_1", "scale_2")]).astype(
            np.float64
        )
    )
    quaternions = np.column_stack(
        [vertex[name] for name in ("rot_0", "rot_1", "rot_2", "rot_3")]
    ).astype(np.float64)
    quaternions /= np.linalg.norm(quaternions, axis=1, keepdims=True).clip(min=1e-12)
    return GaussianCloud(centers, opacity, scales, quaternions)


def rasterize_occupancy(
    cloud: GaussianCloud,
    *,
    opacity_cutoff: float = 0.05,
    spatial_quantile: float = 0.005,
    scale_quantile: float = 0.995,
    maximum_axis_voxels: int = 160,
    sigma_extent: float = 3.0,
) -> OccupancyField:
    """Alpha-compose anisotropic Gaussians into a bounded occupancy grid."""

    if not 0.0 < opacity_cutoff < 1.0:
        raise ValueError("opacity_cutoff must lie between zero and one")
    if not 0.0 <= spatial_quantile < 0.5:
        raise ValueError("spatial_quantile must lie in [0, 0.5)")
    if not 0.0 < scale_quantile <= 1.0:
        raise ValueError("scale_quantile must lie in (0, 1]")
    if maximum_axis_voxels < 24 or sigma_extent <= 0.0:
        raise ValueError("grid resolution and sigma extent are too small")

    opacity_mask = cloud.opacity >= opacity_cutoff
    if int(opacity_mask.sum()) < 1:
        raise ValueError("opacity cutoff retains no Gaussians")
    centers = cloud.centers_m[opacity_mask]
    opacity = cloud.opacity[opacity_mask]
    scales = cloud.scales_m[opacity_mask]
    rotations = cloud.quaternions_wxyz[opacity_mask]

    lower_center = np.quantile(centers, spatial_quantile, axis=0)
    upper_center = np.quantile(centers, 1.0 - spatial_quantile, axis=0)
    spatial_mask = np.all((centers >= lower_center) & (centers <= upper_center), axis=1)
    centers = centers[spatial_mask]
    opacity = opacity[spatial_mask]
    scales = scales[spatial_mask]
    rotations = rotations[spatial_mask]
    if len(centers) < 1:
        raise ValueError("spatial trimming retains no Gaussians")

    maximum_scale = float(np.quantile(scales, scale_quantile))
    scales = np.minimum(scales, maximum_scale)
    padding = sigma_extent * maximum_scale
    lower = centers.min(axis=0) - padding
    upper = centers.max(axis=0) + padding
    spans = upper - lower
    voxel_size = float(spans.max() / (maximum_axis_voxels - 1))
    shape = np.ceil(spans / voxel_size).astype(int) + 1
    values = np.zeros(tuple(int(value) for value in shape), dtype=np.float32)

    for center, alpha, scale, quaternion in zip(centers, opacity, scales, rotations):
        radius = sigma_extent * float(scale.max())
        first = np.maximum(0, np.floor((center - radius - lower) / voxel_size).astype(int))
        last = np.minimum(shape - 1, np.ceil((center + radius - lower) / voxel_size).astype(int))
        axes = [
            lower[axis] + np.arange(first[axis], last[axis] + 1) * voxel_size
            for axis in range(3)
        ]
        xx, yy, zz = np.meshgrid(*axes, indexing="ij")
        delta_world = np.stack((xx - center[0], yy - center[1], zz - center[2]), axis=-1)
        rotation = Rotation.from_quat(
            [quaternion[1], quaternion[2], quaternion[3], quaternion[0]]
        ).as_matrix()
        delta_local = delta_world @ rotation
        mahalanobis = np.sum((delta_local / scale.clip(min=voxel_size / 4.0)) ** 2, axis=-1)
        contribution = float(alpha) * np.exp(-0.5 * mahalanobis)
        slices = tuple(slice(first[axis], last[axis] + 1) for axis in range(3))
        current = values[slices]
        values[slices] = 1.0 - (1.0 - current) * (1.0 - contribution.astype(np.float32))

    return OccupancyField(
        values=values,
        origin_m=lower.astype(np.float64),
        voxel_size_m=voxel_size,
        retained_gaussian_count=len(centers),
        total_gaussian_count=len(cloud.centers_m),
    )


def build_density_collider(
    cloud: GaussianCloud,
    *,
    opacity_cutoff: float = 0.05,
    isovalue: float = 0.15,
    maximum_axis_voxels: int = 160,
    spatial_quantile: float = 0.005,
    scale_quantile: float = 0.995,
    sigma_extent: float = 3.0,
) -> DensityColliderResult:
    """Extract the largest Gaussian-density surface and its convex collider."""

    field = rasterize_occupancy(
        cloud,
        opacity_cutoff=opacity_cutoff,
        spatial_quantile=spatial_quantile,
        scale_quantile=scale_quantile,
        maximum_axis_voxels=maximum_axis_voxels,
        sigma_extent=sigma_extent,
    )
    if not float(field.values.min()) < isovalue < float(field.values.max()):
        raise ValueError("isovalue does not cross the occupancy field")
    vertices, faces, _, _ = measure.marching_cubes(
        field.values,
        level=isovalue,
        spacing=(field.voxel_size_m,) * 3,
        allow_degenerate=False,
    )
    vertices += field.origin_m
    surface = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    components = surface.split(only_watertight=False)
    if not components:
        raise ValueError("marching cubes produced no connected surface")
    surface = max(components, key=lambda mesh: float(mesh.area))
    # The convex hull is the physics-facing simplification.  It is built from the
    # original watertight component because quadric decimation can introduce holes.
    convex = surface.convex_hull
    if not surface.is_watertight or not convex.is_watertight or convex.volume <= 0.0:
        raise ValueError("GS density did not produce a valid watertight collider")
    return DensityColliderResult(field, surface, convex)


def write_density_collider_artifacts(
    cloud: GaussianCloud,
    *,
    optimized_ply: str | Path,
    output_root: str | Path,
    opacity_cutoff: float = 0.05,
    isovalue: float = 0.15,
    maximum_axis_voxels: int = 160,
    spatial_quantile: float = 0.005,
    scale_quantile: float = 0.995,
    sigma_extent: float = 3.0,
) -> Path:
    """Persist a GS-only surface, convex collider, transform, and provenance."""

    optimized_ply = Path(optimized_ply).resolve()
    if not optimized_ply.is_file():
        raise FileNotFoundError(optimized_ply)
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    result = build_density_collider(
        cloud,
        opacity_cutoff=opacity_cutoff,
        isovalue=isovalue,
        maximum_axis_voxels=maximum_axis_voxels,
        spatial_quantile=spatial_quantile,
        scale_quantile=scale_quantile,
        sigma_extent=sigma_extent,
    )

    reconstruction_bounds = result.surface_mesh.bounds
    object_origin = np.asarray(
        [
            float(reconstruction_bounds[:, 0].mean()),
            float(reconstruction_bounds[:, 1].mean()),
            float(reconstruction_bounds[0, 2]),
        ]
    )
    surface = result.surface_mesh.copy()
    collider = result.convex_collider.copy()
    surface.apply_translation(-object_origin)
    collider.apply_translation(-object_origin)

    surface_path = output_root / "gs_density_surface.obj"
    collider_path = output_root / "gs_convex_collider.obj"
    collider_npz_path = output_root / "gs_convex_collider.npz"
    occupancy_path = output_root / "gs_occupancy_field.npz"
    surface.export(surface_path)
    collider.export(collider_path)
    np.savez_compressed(
        collider_npz_path,
        vertices=np.asarray(collider.vertices, dtype=np.float64),
        faces=np.asarray(collider.faces, dtype=np.int32),
        extents=np.asarray(collider.extents, dtype=np.float64),
        volume_m3=np.asarray([collider.volume], dtype=np.float64),
    )
    np.savez_compressed(
        occupancy_path,
        values=result.occupancy.values,
        origin_m=result.occupancy.origin_m,
        voxel_size_m=np.asarray([result.occupancy.voxel_size_m]),
    )

    object_from_reconstruction = np.eye(4, dtype=np.float64)
    object_from_reconstruction[:3, 3] = -object_origin
    manifest = {
        "schema_version": 1,
        "geometry_parent": {
            "type": "optimized_graphdeco_gaussians",
            "path": str(optimized_ply),
            "sha256": _sha256_file(optimized_ply),
            "gaussian_count": int(result.occupancy.total_gaussian_count),
            "retained_gaussian_count": int(result.occupancy.retained_gaussian_count),
        },
        "density": {
            "opacity_cutoff": opacity_cutoff,
            "spatial_quantile": spatial_quantile,
            "scale_quantile": scale_quantile,
            "sigma_extent": sigma_extent,
            "isovalue": isovalue,
            "grid_shape": list(result.occupancy.values.shape),
            "voxel_size_m": result.occupancy.voxel_size_m,
            "path": str(occupancy_path),
            "sha256": _sha256_file(occupancy_path),
        },
        "surface": {
            "path": str(surface_path),
            "sha256": _sha256_file(surface_path),
            "vertices": int(len(surface.vertices)),
            "faces": int(len(surface.faces)),
            "watertight": bool(surface.is_watertight),
        },
        "collider": {
            "type": "single_convex_hull",
            "path": str(collider_path),
            "npz_path": str(collider_npz_path),
            "sha256": _sha256_file(collider_path),
            "npz_sha256": _sha256_file(collider_npz_path),
            "vertices": int(len(collider.vertices)),
            "faces": int(len(collider.faces)),
            "watertight": bool(collider.is_watertight),
            "volume_m3": float(collider.volume),
            "extents_m": [float(value) for value in collider.extents],
        },
        "object_from_reconstruction": object_from_reconstruction.tolist(),
    }
    manifest_path = output_root / "geometry_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path
