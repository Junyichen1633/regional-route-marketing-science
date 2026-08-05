"""Train a first route-active baseline classifier.

This is a diagnostic model, not a final forecasting model. It helps test whether
the current panel has enough signal to support a route opportunity model.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

PANEL_FILE = PROCESSED_DIR / "route_month_panel_v2.csv"

TARGET = "route_active"

NUMERIC_FEATURES = [
    "year",
    "month_num",
    "quarter",
    "is_peak_travel_month",
    "is_regional_origin",
    "is_hub_destination",
    "distance_km",
    "nearest_origin_hub_distance_km",
    "origin_monthly_screened_passengers",
    "destination_monthly_screened_passengers",
    "nearest_origin_hub_monthly_screened_passengers",
    "origin_annual_passengers",
    "destination_annual_passengers",
    "nearest_origin_hub_annual_passengers",
    "origin_domestic_total_itinerant_movements",
    "origin_domestic_air_carrier_level_i_iii_movements",
    "origin_domestic_air_carrier_level_iv_vi_movements",
    "origin_domestic_air_carrier_all_levels_movements",
    "origin_transborder_total_itinerant_movements",
    "origin_other_international_total_itinerant_movements",
    "destination_domestic_total_itinerant_movements",
    "destination_domestic_air_carrier_level_i_iii_movements",
    "destination_domestic_air_carrier_level_iv_vi_movements",
    "destination_domestic_air_carrier_all_levels_movements",
    "destination_transborder_total_itinerant_movements",
    "destination_other_international_total_itinerant_movements",
    "nearest_origin_hub_domestic_total_itinerant_movements",
    "nearest_origin_hub_domestic_air_carrier_level_i_iii_movements",
    "nearest_origin_hub_domestic_air_carrier_level_iv_vi_movements",
    "nearest_origin_hub_domestic_air_carrier_all_levels_movements",
    "nearest_origin_hub_transborder_total_itinerant_movements",
    "nearest_origin_hub_other_international_total_itinerant_movements",
]

CATEGORICAL_FEATURES = [
    "origin_iata",
    "destination_iata",
    "origin_province",
    "destination_province",
    "season",
    "covid_period",
    "route_group",
    "strategic_role",
    "status_assumption",
    "route_segment",
    "nearest_origin_hub_iata",
]


def read_rows() -> list[dict[str, str]]:
    with PANEL_FILE.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str) -> float:
    if value == "":
        return np.nan
    return float(value)


def build_matrix(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray, list[dict[str, str]]]:
    labeled = [row for row in rows if row[TARGET] in ("0", "1")]
    feature_rows = []
    for row in labeled:
        feature_row = {}
        for feature in NUMERIC_FEATURES:
            feature_row[feature] = to_float(row.get(feature, ""))
        for feature in CATEGORICAL_FEATURES:
            feature_row[feature] = row.get(feature, "")
        feature_rows.append(feature_row)

    matrix = np.array([[row[feature] for feature in NUMERIC_FEATURES + CATEGORICAL_FEATURES] for row in feature_rows], dtype=object)
    target = np.array([int(row[TARGET]) for row in labeled])
    return matrix, target, labeled


def build_pipeline() -> Pipeline:
    numeric_indices = list(range(len(NUMERIC_FEATURES)))
    categorical_indices = list(range(len(NUMERIC_FEATURES), len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES)))
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_indices,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_indices,
            ),
        ]
    )
    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])


def metric_dict(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float | int | None]:
    metrics: dict[str, float | int | None] = {
        "n": int(len(y_true)),
        "positive_rate": float(np.mean(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": None,
    }
    if len(np.unique(y_true)) == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    return metrics


def evaluate_temporal_holdout(matrix: np.ndarray, target: np.ndarray, rows: list[dict[str, str]]) -> dict[str, object]:
    train_mask = np.array([int(row["year"]) <= 2024 for row in rows])
    test_mask = np.array([int(row["year"]) == 2025 for row in rows])
    if train_mask.sum() == 0 or test_mask.sum() == 0:
        raise ValueError("Temporal holdout split is empty.")

    pipeline = build_pipeline()
    pipeline.fit(matrix[train_mask], target[train_mask])
    test_prob = pipeline.predict_proba(matrix[test_mask])[:, 1]
    test_pred = (test_prob >= 0.5).astype(int)
    train_prob = pipeline.predict_proba(matrix[train_mask])[:, 1]
    train_pred = (train_prob >= 0.5).astype(int)

    return {
        "train": metric_dict(target[train_mask], train_pred, train_prob),
        "test_2025": metric_dict(target[test_mask], test_pred, test_prob),
    }


def summarize_labels(rows: list[dict[str, str]]) -> dict[str, object]:
    labeled = [row for row in rows if row[TARGET] in ("0", "1")]
    by_route: dict[str, dict[str, int]] = {}
    for row in rows:
        route_id = row["route_id"]
        by_route.setdefault(route_id, {"active": 0, "inactive": 0, "uncovered": 0})
        if row[TARGET] == "1":
            by_route[route_id]["active"] += 1
        elif row[TARGET] == "0":
            by_route[route_id]["inactive"] += 1
        else:
            by_route[route_id]["uncovered"] += 1

    return {
        "rows": len(rows),
        "labeled_rows": len(labeled),
        "label_coverage": len(labeled) / len(rows),
        "positive_rate_labeled": sum(1 for row in labeled if row[TARGET] == "1") / len(labeled),
        "by_route": by_route,
    }


def write_outputs(metrics: dict[str, object], label_summary: dict[str, object]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "route_active_baseline_metrics.json").write_text(
        json.dumps({"metrics": metrics, "label_summary": label_summary}, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Route-Active Baseline V0",
        "",
        "This diagnostic model uses a logistic regression classifier with structural route features and airport-month movement context.",
        "",
        "Important caveat: route-active labels come from a sourced manual event layer, not a complete schedule archive.",
        "",
        "## Label Summary",
        "",
        f"- Total rows: {label_summary['rows']:,}",
        f"- Labeled rows: {label_summary['labeled_rows']:,}",
        f"- Label coverage: {label_summary['label_coverage']:.1%}",
        f"- Positive rate among labeled rows: {label_summary['positive_rate_labeled']:.1%}",
        "",
        "## Temporal Holdout",
        "",
        "| Split | N | Positive rate | Accuracy | Precision | Recall | F1 | ROC AUC |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for split_name in ["train", "test_2025"]:
        split = metrics[split_name]
        auc = split["roc_auc"]
        auc_text = "" if auc is None else f"{auc:.3f}"
        lines.append(
            "| "
            f"{split_name} | {split['n']} | {split['positive_rate']:.1%} | "
            f"{split['accuracy']:.3f} | {split['precision']:.3f} | "
            f"{split['recall']:.3f} | {split['f1']:.3f} | {auc_text} |"
        )

    lines.extend(
        [
            "",
            "## Route Label Coverage",
            "",
            "| Route | Active | Inactive | Uncovered |",
            "|---|---:|---:|---:|",
        ]
    )
    by_route = label_summary["by_route"]
    for route_id in sorted(by_route):
        counts = by_route[route_id]
        lines.append(
            f"| {route_id} | {counts['active']} | {counts['inactive']} | {counts['uncovered']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The baseline is useful as a diagnostic, not as a final route decision model.",
            "- The next modeling improvement is to reduce uncovered route-months and avoid over-reliance on route identity proxies.",
            "- The final portfolio narrative should emphasize data limitations and the experiment plan rather than overclaiming predictive accuracy.",
            "",
        ]
    )
    (OUTPUTS_DIR / "route_active_baseline_v0.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = read_rows()
    matrix, target, labeled_rows = build_matrix(rows)
    metrics = evaluate_temporal_holdout(matrix, target, labeled_rows)
    label_summary = summarize_labels(rows)
    write_outputs(metrics, label_summary)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

