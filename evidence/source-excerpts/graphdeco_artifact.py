"""Independent validation of optimized Graphdeco Gaussian artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_GAUSSIAN_FIELDS = {
    "x",
    "y",
    "z",
    "f_dc_0",
    "f_dc_1",
    "f_dc_2",
    "opacity",
    "scale_0",
    "scale_1",
    "scale_2",
    "rot_0",
    "rot_1",
    "rot_2",
    "rot_3",
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def read_ply_vertex_header(path: Path) -> tuple[int, list[str]]:
    vertex_count: int | None = None
    fields: list[str] = []
    in_vertex = False
    with path.open("rb") as stream:
        first = stream.readline()
        if first.rstrip(b"\r\n") != b"ply":
            raise ValueError(f"not a PLY file: {path}")
        for raw_line in stream:
            try:
                line = raw_line.decode("ascii").strip()
            except UnicodeDecodeError as error:
                raise ValueError(f"PLY header is not ASCII: {path}") from error
            if line == "end_header":
                break
            if line.startswith("element "):
                tokens = line.split()
                in_vertex = len(tokens) == 3 and tokens[1] == "vertex"
                if in_vertex:
                    vertex_count = int(tokens[2])
            elif in_vertex and line.startswith("property "):
                tokens = line.split()
                if len(tokens) >= 3:
                    fields.append(tokens[-1])
        else:
            raise ValueError(f"PLY header has no end_header marker: {path}")
    if vertex_count is None:
        raise ValueError(f"PLY header has no vertex element: {path}")
    return vertex_count, fields


def verify_graphdeco_artifact(
    *,
    optimized_ply: str | Path,
    initialization_ply: str | Path,
    training_log: str | Path,
    expected_iteration: int,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    optimized_ply = Path(optimized_ply).resolve()
    initialization_ply = Path(initialization_ply).resolve()
    training_log = Path(training_log).resolve()

    expected_directory = f"iteration_{expected_iteration}"
    if (
        optimized_ply.name != "point_cloud.ply"
        or optimized_ply.parent.name != expected_directory
        or optimized_ply.parent.parent.name != "point_cloud"
    ):
        raise ValueError(
            f"optimized artifact must be in a point_cloud/{expected_directory} iteration directory"
        )

    for label, path in (
        ("optimized PLY", optimized_ply),
        ("initialization PLY", initialization_ply),
        ("training log", training_log),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"{label} does not exist: {path}")

    optimized_sha = sha256_file(optimized_ply)
    initialization_sha = sha256_file(initialization_ply)
    if optimized_sha == initialization_sha:
        raise ValueError("optimized PLY is byte-identical to initialization")

    vertex_count, fields = read_ply_vertex_header(optimized_ply)
    if vertex_count <= 0:
        raise ValueError("optimized PLY contains no Gaussian vertices")
    missing = sorted(REQUIRED_GAUSSIAN_FIELDS.difference(fields))
    if missing:
        raise ValueError(f"optimized PLY is missing Gaussian properties: {missing}")

    log_text = training_log.read_text(encoding="utf-8", errors="replace")
    marker = re.compile(rf"\[ITER\s+{expected_iteration}\]\s+Saving Gaussians")
    if marker.search(log_text) is None:
        raise ValueError(f"training log does not prove iteration {expected_iteration}")

    report: dict[str, Any] = {
        "schema_version": 1,
        "verified": True,
        "iteration": expected_iteration,
        "optimized_ply": str(optimized_ply),
        "initialization_ply": str(initialization_ply),
        "training_log": str(training_log),
        "vertex_count": vertex_count,
        "fields": fields,
        "optimized_sha256": optimized_sha,
        "initialization_sha256": initialization_sha,
    }
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return report
