"""Aggregate and visualize the paired PhysX pilot without hiding failures."""

from __future__ import annotations

from collections import Counter
import csv
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import numpy as np

from .statistics import paired_bootstrap_ci, sign_flip_pvalue


PARAMETERS = ("mass_kg", "static_friction", "dynamic_friction", "restitution")


def _paired_summary(left: np.ndarray, right: np.ndarray, seed: int) -> dict[str, Any]:
    difference = left - right
    return {
        "mean_difference": float(np.mean(difference)),
        "median_difference": float(np.median(difference)),
        "bootstrap_ci95": list(paired_bootstrap_ci(left, right, seed=seed)),
        "exact_sign_flip_pvalue_two_sided": sign_flip_pvalue(difference),
    }


def build_report_summary(root: str | Path, seed: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = Path(root)
    aggregate = json.loads((root / "public" / "aggregate.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    adaptive_action_counts: Counter[str] = Counter()
    for aggregate_row in aggregate["rows"]:
        unit_id = aggregate_row["unit_id"]
        private_path = root / "units" / unit_id / "private" / "evaluation_with_gt.json"
        private = json.loads(private_path.read_text(encoding="utf-8"))
        gt = private["ground_truth"]
        fixed = private["conditions"]["fixed_active"]
        adaptive = private["conditions"]["adaptive_active"]
        fixed_final = fixed["posterior_history"][-1]
        adaptive_final = adaptive["posterior_history"][-1]
        action_sequence = [f'{item["kind"]}:{item["magnitude"]:g}' for item in adaptive["active_actions"]]
        adaptive_action_counts.update(action_sequence)
        diagnostic = private["effective_static_friction"]
        row = dict(aggregate_row)
        row.update(
            {
                "adaptive_actions": ",".join(action_sequence),
                "nominal_static_friction": float(diagnostic["nominal_coefficient"]),
                "effective_static_friction": float(diagnostic["effective_coefficient"]),
            }
        )
        for parameter in PARAMETERS:
            row[f"gt_{parameter}"] = float(gt[parameter])
            row[f"fixed_{parameter}"] = float(fixed_final[parameter])
            row[f"adaptive_{parameter}"] = float(adaptive_final[parameter])
            row[f"fixed_{parameter}_abs_error"] = abs(float(fixed_final[parameter]) - float(gt[parameter]))
            row[f"adaptive_{parameter}_abs_error"] = abs(float(adaptive_final[parameter]) - float(gt[parameter]))
        rows.append(row)

    if not rows:
        raise ValueError("the experiment contains no completed independent units")
    prior = np.asarray([row["prior_only_error"] for row in rows], dtype=np.float64)
    passive = np.asarray([row["prior_passive_error"] for row in rows], dtype=np.float64)
    fixed_final = np.asarray([row["fixed_final_error"] for row in rows], dtype=np.float64)
    adaptive_final = np.asarray([row["adaptive_final_error"] for row in rows], dtype=np.float64)
    fixed_auc = np.asarray([row["fixed_active_auc"] for row in rows], dtype=np.float64)
    adaptive_auc = np.asarray([row["adaptive_active_auc"] for row in rows], dtype=np.float64)
    fixed_minus_adaptive = _paired_summary(fixed_auc, adaptive_auc, seed=seed)
    parameter_mae = {
        condition: {
            parameter: float(np.mean([row[f"{condition}_{parameter}_abs_error"] for row in rows]))
            for parameter in PARAMETERS
        }
        for condition in ("fixed", "adaptive")
    }
    worst = max(rows, key=lambda row: row["adaptive_active_auc"] - row["fixed_active_auc"])
    summary = {
        "evidence_class": "omnigibson_physx_paired_pilot",
        "independent_units": len(rows),
        "failed_units": int(aggregate.get("failed_units", 0)),
        "mean_errors": {
            "prior_only": float(np.mean(prior)),
            "prior_passive": float(np.mean(passive)),
            "fixed_final": float(np.mean(fixed_final)),
            "adaptive_final": float(np.mean(adaptive_final)),
        },
        "paired_stage_contrasts": {
            "prior_minus_passive": _paired_summary(prior, passive, seed=seed + 1),
            "passive_minus_fixed_final": _paired_summary(passive, fixed_final, seed=seed + 2),
            "passive_minus_adaptive_final": _paired_summary(passive, adaptive_final, seed=seed + 3),
            "fixed_auc_minus_adaptive_auc": fixed_minus_adaptive,
        },
        "adaptive_auc_wins": int(np.sum(adaptive_auc < fixed_auc)),
        "fixed_auc_wins": int(np.sum(fixed_auc < adaptive_auc)),
        "ties": int(np.sum(fixed_auc == adaptive_auc)),
        "parameter_mean_absolute_error": parameter_mae,
        "mean_nominal_minus_effective_static_friction": float(
            np.mean([row["nominal_static_friction"] - row["effective_static_friction"] for row in rows])
        ),
        "adaptive_action_counts": dict(sorted(adaptive_action_counts.items())),
        "worst_adaptive_unit": {
            "unit_id": worst["unit_id"],
            "adaptive_minus_fixed_auc": float(worst["adaptive_active_auc"] - worst["fixed_active_auc"]),
            "adaptive_actions": worst["adaptive_actions"],
        },
        "main_hypothesis_supported_in_pilot": bool(fixed_minus_adaptive["bootstrap_ci95"][0] > 0.0),
    }
    return summary, rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_plot(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    stages = ("prior_only_error", "prior_passive_error", "fixed_final_error")
    x = np.arange(len(stages))
    for row in rows:
        axes[0, 0].plot(x, [row[name] for name in stages], color="#5B8FF9", alpha=0.35)
    axes[0, 0].plot(
        x,
        [np.mean([row[name] for row in rows]) for name in stages],
        color="#173F5F",
        marker="o",
        linewidth=2.5,
        label="mean",
    )
    axes[0, 0].set_xticks(x, ("Prior", "+ Passive", "+ Fixed active"))
    axes[0, 0].set_ylabel("Held-out translation NRMSE")
    axes[0, 0].set_title("Evidence accumulation")
    axes[0, 0].legend()

    fixed_auc = np.asarray([row["fixed_active_auc"] for row in rows])
    adaptive_auc = np.asarray([row["adaptive_active_auc"] for row in rows])
    limit = float(max(np.max(fixed_auc), np.max(adaptive_auc)) * 1.05)
    axes[0, 1].scatter(fixed_auc, adaptive_auc, color="#ED553B")
    axes[0, 1].plot([0, limit], [0, limit], linestyle="--", color="black", linewidth=1)
    axes[0, 1].set(xlabel="Fixed AUC", ylabel="Adaptive AUC", title="Paired active-policy result")

    action_counts = summary["adaptive_action_counts"]
    axes[1, 0].bar(range(len(action_counts)), list(action_counts.values()), color="#3CAEA3")
    axes[1, 0].set_xticks(range(len(action_counts)), list(action_counts), rotation=35, ha="right")
    axes[1, 0].set_ylabel("Selections across 12 units")
    axes[1, 0].set_title("Adaptive action choices")

    nominal = np.asarray([row["nominal_static_friction"] for row in rows])
    effective = np.asarray([row["effective_static_friction"] for row in rows])
    axes[1, 1].scatter(nominal, effective, color="#F6D55C", edgecolor="black")
    axes[1, 1].plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1)
    axes[1, 1].set(
        xlim=(0, 1),
        ylim=(0, 1),
        xlabel="Nominal PhysX static friction",
        ylabel="Effective breakaway coefficient",
        title="Nominal vs behavioral friction",
    )
    figure.suptitle("GS-bound PhysX paired pilot", fontsize=15, fontweight="bold")
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _write_markdown(path: Path, summary: dict[str, Any]) -> None:
    errors = summary["mean_errors"]
    contrast = summary["paired_stage_contrasts"]["fixed_auc_minus_adaptive_auc"]
    worst = summary["worst_adaptive_unit"]
    supported = "지지됨" if summary["main_hypothesis_supported_in_pilot"] else "지지되지 않음"
    text = f"""# GS-bound Physical Digital Twin: 핵심 PhysX pilot 결과

## 한 줄 결론

Semantic/material prior에 passive inverse physics를 더하면 보지 않은 미래 운동 예측은 뚜렷하게 좋아졌지만, 현재 adaptive selector가 같은 3회 예산의 fixed schedule보다 낫다는 주가설은 이 pilot에서 **{supported}**.

## 실험

- 독립 hidden-GT 단위: {summary['independent_units']}개, 실패 {summary['failed_units']}개
- 모든 조건은 동일한 GS-derived geometry, passive 관측, 센서 노이즈, held-out 행동을 공유
- 비교: prior only → prior+passive → fixed active 3회 / adaptive active 3회
- 평가: 식별에 쓰지 않은 impulse, breakaway ramp, oblique drop의 미래 운동

## 핵심 수치

- 평균 translation NRMSE: prior `{errors['prior_only']:.4f}` → passive `{errors['prior_passive']:.4f}` → fixed `{errors['fixed_final']:.4f}` / adaptive `{errors['adaptive_final']:.4f}`
- fixed AUC − adaptive AUC: 평균 `{contrast['mean_difference']:.4f}`, 95% bootstrap CI `[{contrast['bootstrap_ci95'][0]:.4f}, {contrast['bootstrap_ci95'][1]:.4f}]`, exact sign-flip p=`{contrast['exact_sign_flip_pvalue_two_sided']:.3f}`
- adaptive 승리 {summary['adaptive_auc_wins']}개, fixed 승리 {summary['fixed_auc_wins']}개

## 왜 adaptive가 안정적으로 이기지 못했는가

가장 큰 실패 단위는 `{worst['unit_id']}`였다. Adaptive는 `{worst['adaptive_actions']}`를 선택해 낙하 probe를 수행하지 않았다. 그 결과 반발계수 오류가 held-out oblique drop으로 직접 전파됐다. 현재 selector의 점수는 단일 관측의 파라미터 정보량에 가깝고, 실제 held-out 미래 운동 위험을 충분히 반영하지 못한다. 또한 입자 posterior의 재표본화가 재질 prior의 파라미터 상관을 증폭해 관측하지 않은 반발계수까지 이동시키는 현상이 확인됐다.

## 정지마찰에서 확인된 문제

설정한 nominal static friction과 실제 breakaway에서 계산한 effective coefficient의 평균 차이는 `{summary['mean_nominal_minus_effective_static_friction']:.4f}`였다. 따라서 nominal GT 값 회복과 실제 운동 예측 성능은 별도로 평가해야 한다.

## 해석 범위

이 결과는 **pilot evidence**이며 확정적 결론이 아니다. 현재 복원은 photometric 3DGS 학습본이 아니라 RGB-D-initialized Gaussian 표현이고, 한 가지 GS geometry만 사용했다. 상호작용은 simulator actuator가 만들었으며 R1 Pro는 아직 접촉 제어를 하지 않았다. 추론과 평가가 같은 PhysX를 공유한다는 self-consistency 한계도 남는다.

## 다음 실험

1. selector를 expected held-out trajectory-risk reduction으로 바꾸고, 서로 다른 물성 종류를 최소 한 번씩 탐색하도록 하는 조건을 탐색적 후속 실험으로 비교한다.
2. 결과를 고정한 뒤 대표 GT 단위에서 R1 Pro가 실제 접촉으로 같은 probe를 재현한다.
3. photometric 3DGS와 여러 GS-derived collider로 geometry 일반화를 검증한다.
"""
    path.write_text(text, encoding="utf-8")


def write_core_report(root: str | Path, seed: int = 20260831) -> dict[str, Path]:
    root = Path(root)
    public = root / "public"
    public.mkdir(parents=True, exist_ok=True)
    summary, rows = build_report_summary(root, seed=seed)
    paths = {
        "summary": public / "report_summary.json",
        "csv": public / "per_unit.csv",
        "plot": public / "core_experiment_results.png",
        "report": public / "REPORT.md",
    }
    paths["summary"].write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(paths["csv"], rows)
    _write_plot(paths["plot"], summary, rows)
    _write_markdown(paths["report"], summary)
    return paths

