"""Run marketing sensitivity and recovery simulations.

The project does not have observed marketing spend. This script tests whether a
simple marketing model can recover the correct channel ranking and budget
direction under different simulated data-generating mechanisms.
"""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"

CHANNEL_FILE = CONFIG_DIR / "marketing_channel_truth_assumptions.csv"
SCENARIO_FILE = CONFIG_DIR / "marketing_sensitivity_scenarios.csv"
PANEL_FILE = PROCESSED_DIR / "route_month_panel_v2.csv"
ROUTE_SCORE_FILE = PROCESSED_DIR / "route_opportunity_score_v0.csv"
ROUTE_RESPONSE_FILE = PROCESSED_DIR / "marketing_response_route_summary_v0.csv"

REPLICATE_FILE = PROCESSED_DIR / "marketing_sensitivity_replicates_v0.csv"
SUMMARY_CSV_FILE = PROCESSED_DIR / "marketing_sensitivity_summary_v0.csv"
SUMMARY_MD_FILE = OUTPUTS_DIR / "marketing_sensitivity_analysis_v0_summary.md"
REPORT_FILE = REPORTS_DIR / "phase4b_marketing_sensitivity_memo.md"

ANALYSIS_START_YEAR = 2023
ANALYSIS_END_YEAR = 2025
MODEL_SPECS = ["naive_raw_spend", "controlled_adstock", "controlled_saturation"]
BUDGET_DIRECTION_WEIGHTS = [0.45, 0.30, 0.15, 0.10]
RANDOM_SEED = 20260805


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def to_int(value: str | None, default: int = 0) -> int:
    return int(round(to_float(value, float(default))))


def normalize_shares(raw: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in raw.values())
    if total <= 0:
        equal = 1.0 / len(raw)
        return {key: equal for key in raw}
    return {key: max(0.0, value) / total for key, value in raw.items()}


def route_score_lookup() -> dict[str, dict[str, str]]:
    return {row["route_id"]: row for row in read_csv(ROUTE_SCORE_FILE)}


def baseline_proxy_lookup() -> dict[str, float]:
    lookup = {}
    for row in read_csv(ROUTE_RESPONSE_FILE):
        if row["scenario"] == "base":
            lookup[row["route_id"]] = to_float(row["baseline_annual_passenger_proxy"])
    return lookup


def channel_assumptions() -> list[dict[str, object]]:
    channels = []
    for row in read_csv(CHANNEL_FILE):
        channels.append(
            {
                "channel": row["channel"],
                "true_rank": to_int(row["true_rank"]),
                "max_lift_pct": to_float(row["max_lift_pct"]),
                "half_saturation_monthly_spend_cad": to_float(row["half_saturation_monthly_spend_cad"]),
                "adstock_decay": to_float(row["adstock_decay"]),
                "default_budget_share": to_float(row["default_budget_share"]),
            }
        )
    channels.sort(key=lambda row: int(row["true_rank"]))
    return channels


def scenario_rows() -> list[dict[str, str]]:
    return read_csv(SCENARIO_FILE)


def prepared_panel() -> list[dict[str, object]]:
    scores = route_score_lookup()
    baselines = baseline_proxy_lookup()
    rows = []

    for row in read_csv(PANEL_FILE):
        year = to_int(row.get("year"))
        route_id = row["route_id"]
        if year < ANALYSIS_START_YEAR or year > ANALYSIS_END_YEAR:
            continue
        score_row = scores.get(route_id)
        if score_row is None or score_row.get("model_role") != "target":
            continue
        if route_id not in baselines:
            continue

        route_active = row.get("route_active", "")
        if route_active == "1":
            active_multiplier = 1.00
        elif route_active == "0":
            active_multiplier = 0.22
        else:
            active_multiplier = 0.70

        month_num = to_int(row.get("month_num"))
        peak_multiplier = 1.16 if row.get("is_peak_travel_month") == "1" else 0.96
        winter_drag = 0.93 if row.get("season") == "winter" else 1.0
        monthly_baseline = (baselines[route_id] / 12.0) * active_multiplier * peak_multiplier * winter_drag

        rows.append(
            {
                "route_id": route_id,
                "month": row["month"],
                "year": year,
                "month_num": month_num,
                "season": row.get("season", ""),
                "is_peak": 1 if row.get("is_peak_travel_month") == "1" else 0,
                "route_active": route_active,
                "baseline_passenger_proxy": monthly_baseline,
                "annual_baseline_proxy": baselines[route_id],
                "demand_context_score": to_float(score_row.get("demand_context_score")),
                "route_sustainability_score_v0": to_float(score_row.get("route_sustainability_score_v0")),
                "marketing_support_priority_score_v0": to_float(score_row.get("marketing_support_priority_score_v0")),
                "data_confidence_score": to_float(score_row.get("data_confidence_score")),
                "competition_pressure_score": to_float(score_row.get("competition_pressure_score")),
                "end_of_period_route_status": score_row.get("end_of_period_route_status", ""),
                "route_segment": score_row.get("route_segment", ""),
            }
        )
    rows.sort(key=lambda row: (str(row["route_id"]), str(row["month"])))
    return rows


def route_month_shock(row: dict[str, object], mechanism: str, rng: random.Random) -> float:
    baseline = float(row["baseline_passenger_proxy"])
    peak = float(row["is_peak"])
    priority = float(row["marketing_support_priority_score_v0"]) / 100.0
    sustainability = float(row["route_sustainability_score_v0"]) / 100.0

    if mechanism == "demand_following":
        return baseline * (0.05 * peak + 0.04 * priority)
    if mechanism == "risk_targeting":
        return -baseline * (0.07 * (1.0 - sustainability) + 0.03 * (1.0 - priority))
    if mechanism == "seasonal_campaign":
        return baseline * (0.06 * peak + 0.03 * (row["month_num"] in {3, 4, 5, 9}))
    if mechanism == "channel_bundle":
        return baseline * rng.uniform(-0.025, 0.025)
    return baseline * rng.uniform(-0.015, 0.015)


def route_total_spend(row: dict[str, object], mechanism: str, rng: random.Random) -> float:
    baseline_scale = min(float(row["annual_baseline_proxy"]) / 140_000.0, 1.2)
    priority = float(row["marketing_support_priority_score_v0"]) / 100.0
    sustainability = float(row["route_sustainability_score_v0"]) / 100.0
    peak = float(row["is_peak"])
    active_bonus = 0.85 if row["route_active"] == "0" else 1.0

    if mechanism == "randomized":
        spend = rng.uniform(2_000, 24_000)
    elif mechanism == "demand_following":
        spend = 3_000 + 12_000 * baseline_scale + 9_000 * peak + 6_000 * priority
        spend *= rng.uniform(0.75, 1.25)
    elif mechanism == "risk_targeting":
        spend = 3_000 + 15_000 * (1.0 - sustainability) + 7_000 * (1.0 - priority) + 4_000 * (1.0 - peak)
        spend *= active_bonus * rng.uniform(0.75, 1.30)
    elif mechanism == "seasonal_campaign":
        campaign_month = row["month_num"] in {2, 3, 4, 5, 9, 10}
        spend = 2_500 + 15_000 * campaign_month + 8_000 * peak + 3_000 * baseline_scale
        spend *= rng.uniform(0.85, 1.20)
    elif mechanism == "channel_bundle":
        spend = 4_000 + 8_000 * baseline_scale + 7_000 * priority + 5_000 * peak
        spend *= rng.uniform(0.90, 1.10)
    else:
        raise ValueError(f"Unsupported mechanism: {mechanism}")

    return max(0.0, min(spend, 35_000.0))


def channel_shares(
    row: dict[str, object],
    mechanism: str,
    channels: list[dict[str, object]],
    rng: random.Random,
) -> dict[str, float]:
    default = {str(channel["channel"]): float(channel["default_budget_share"]) for channel in channels}
    month = int(row["month_num"])

    if mechanism == "randomized":
        return normalize_shares({name: share * rng.uniform(0.45, 1.65) for name, share in default.items()})
    if mechanism == "demand_following":
        raw = dict(default)
        raw["paid_search"] *= 1.20 if row["is_peak"] else 1.00
        raw["paid_social"] *= 1.15
        raw["local_ooh"] *= 0.85
        return normalize_shares(raw)
    if mechanism == "risk_targeting":
        raw = dict(default)
        raw["paid_social"] *= 1.35
        raw["display_video"] *= 1.25
        raw["paid_search"] *= 0.85
        return normalize_shares(raw)
    if mechanism == "seasonal_campaign":
        raw = dict(default)
        raw["local_ooh"] *= 1.45 if month in {2, 3, 4, 5} else 0.90
        raw["paid_search"] *= 1.25 if row["is_peak"] else 0.95
        raw["display_video"] *= 1.20 if month in {9, 10} else 0.90
        return normalize_shares(raw)
    if mechanism == "channel_bundle":
        return normalize_shares({name: share * rng.uniform(0.92, 1.08) for name, share in default.items()})
    raise ValueError(f"Unsupported mechanism: {mechanism}")


def simulate_dataset(
    panel_rows: list[dict[str, object]],
    channels: list[dict[str, object]],
    scenario: dict[str, str],
    replicate: int,
) -> tuple[list[dict[str, object]], dict[str, float]]:
    mechanism = scenario["spend_mechanism"]
    effect_multiplier = to_float(scenario["effect_multiplier"])
    noise_pct = to_float(scenario["noise_pct"])
    rng = random.Random(RANDOM_SEED + replicate * 997 + sum(ord(char) for char in scenario["scenario_id"]))

    channel_names = [str(channel["channel"]) for channel in channels]
    channel_by_name = {str(channel["channel"]): channel for channel in channels}
    simulated = []

    for source in panel_rows:
        row = dict(source)
        total_spend = route_total_spend(row, mechanism, rng)
        shares = channel_shares(row, mechanism, channels, rng)
        for channel_name in channel_names:
            row[f"spend_{channel_name}"] = total_spend * shares[channel_name]
        simulated.append(row)

    prev_adstock: dict[tuple[str, str], float] = defaultdict(float)
    for row in simulated:
        route_id = str(row["route_id"])
        for channel_name in channel_names:
            channel = channel_by_name[channel_name]
            raw_spend = float(row[f"spend_{channel_name}"])
            key = (route_id, channel_name)
            adstock = raw_spend + float(channel["adstock_decay"]) * prev_adstock[key]
            row[f"adstock_{channel_name}"] = adstock
            prev_adstock[key] = adstock

    true_incremental_by_channel = {channel_name: 0.0 for channel_name in channel_names}
    spend_by_channel = {channel_name: 0.0 for channel_name in channel_names}

    for row in simulated:
        baseline = float(row["baseline_passenger_proxy"])
        true_incremental_total = 0.0
        for channel_name in channel_names:
            channel = channel_by_name[channel_name]
            adstock = float(row[f"adstock_{channel_name}"])
            response_share = adstock / (adstock + float(channel["half_saturation_monthly_spend_cad"])) if adstock > 0 else 0.0
            incremental = baseline * float(channel["max_lift_pct"]) * effect_multiplier * response_share
            row[f"true_incremental_{channel_name}"] = incremental
            true_incremental_by_channel[channel_name] += incremental
            spend_by_channel[channel_name] += float(row[f"spend_{channel_name}"])
            true_incremental_total += incremental

        shock = route_month_shock(row, mechanism, rng)
        noise = rng.gauss(0.0, max(1.0, baseline * noise_pct))
        row["true_incremental_total"] = true_incremental_total
        row["unobserved_demand_shock"] = shock
        row["observed_passenger_proxy"] = max(0.0, baseline + true_incremental_total + shock + noise)

    true_roi = {
        channel_name: true_incremental_by_channel[channel_name] / max(spend_by_channel[channel_name], 1.0)
        for channel_name in channel_names
    }
    return simulated, true_roi


def design_matrix(
    rows: list[dict[str, object]],
    channels: list[dict[str, object]],
    model_spec: str,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    channel_names = [str(channel["channel"]) for channel in channels]
    channel_by_name = {str(channel["channel"]): channel for channel in channels}
    feature_names = ["intercept"]
    columns = [np.ones(len(rows))]

    for channel_name in channel_names:
        feature_names.append(channel_name)
        if model_spec == "naive_raw_spend":
            columns.append(np.array([float(row[f"spend_{channel_name}"]) / 10_000.0 for row in rows]))
        elif model_spec == "controlled_adstock":
            columns.append(np.array([float(row[f"adstock_{channel_name}"]) / 10_000.0 for row in rows]))
        elif model_spec == "controlled_saturation":
            half_saturation = float(channel_by_name[channel_name]["half_saturation_monthly_spend_cad"])
            columns.append(
                np.array(
                    [
                        float(row["baseline_passenger_proxy"])
                        * (
                            float(row[f"adstock_{channel_name}"])
                            / (float(row[f"adstock_{channel_name}"]) + half_saturation)
                            if float(row[f"adstock_{channel_name}"]) > 0
                            else 0.0
                        )
                        for row in rows
                    ]
                )
            )
        else:
            raise ValueError(f"Unsupported model spec: {model_spec}")

    if model_spec in {"controlled_adstock", "controlled_saturation"}:
        route_ids = sorted({str(row["route_id"]) for row in rows})
        month_nums = sorted({int(row["month_num"]) for row in rows})
        for route_id in route_ids[1:]:
            feature_names.append(f"route_{route_id}")
            columns.append(np.array([1.0 if row["route_id"] == route_id else 0.0 for row in rows]))
        for month_num in month_nums[1:]:
            feature_names.append(f"month_{month_num}")
            columns.append(np.array([1.0 if int(row["month_num"]) == month_num else 0.0 for row in rows]))
        feature_names.append("route_active_label")
        columns.append(np.array([1.0 if row["route_active"] == "1" else 0.0 for row in rows]))
        feature_names.append("peak_month")
        columns.append(np.array([float(row["is_peak"]) for row in rows]))

    x = np.column_stack(columns)
    y = np.array([float(row["observed_passenger_proxy"]) for row in rows])
    return x, y, feature_names


def fit_ridge_coefficients(
    rows: list[dict[str, object]],
    channels: list[dict[str, object]],
    model_spec: str,
) -> dict[str, float]:
    x, y, feature_names = design_matrix(rows, channels, model_spec)
    channel_names = [str(channel["channel"]) for channel in channels]
    alpha = 0.01 if model_spec == "controlled_saturation" else 0.25 if model_spec == "controlled_adstock" else 0.05
    penalty = np.eye(x.shape[1]) * alpha
    penalty[0, 0] = 0.0
    beta = np.linalg.pinv(x.T @ x + penalty) @ x.T @ y
    coefficient_by_name = {feature_names[index]: float(beta[index]) for index in range(len(feature_names))}
    return {channel: coefficient_by_name[channel] for channel in channel_names}


def rank_dict(scores: dict[str, float], descending: bool = True) -> dict[str, int]:
    ordered = sorted(scores, key=lambda key: (-scores[key], key) if descending else (scores[key], key))
    return {channel: rank for rank, channel in enumerate(ordered, start=1)}


def spearman_rank_corr(true_scores: dict[str, float], estimated_scores: dict[str, float]) -> float:
    true_ranks = rank_dict(true_scores, descending=True)
    estimated_ranks = rank_dict(estimated_scores, descending=True)
    channels = sorted(true_scores)
    n = len(channels)
    squared_diff = sum((true_ranks[channel] - estimated_ranks[channel]) ** 2 for channel in channels)
    return 1.0 - (6.0 * squared_diff) / (n * (n**2 - 1))


def allocation_weights(ranked_channels: list[str]) -> dict[str, float]:
    return {
        channel: BUDGET_DIRECTION_WEIGHTS[index]
        for index, channel in enumerate(ranked_channels)
    }


def recovery_metrics(true_roi: dict[str, float], estimated_coefficients: dict[str, float]) -> dict[str, object]:
    true_ranked = sorted(true_roi, key=lambda key: (-true_roi[key], key))
    estimated_ranked = sorted(estimated_coefficients, key=lambda key: (-estimated_coefficients[key], key))
    true_top2 = set(true_ranked[:2])
    estimated_top2 = set(estimated_ranked[:2])

    true_weights = allocation_weights(true_ranked)
    estimated_weights = allocation_weights(estimated_ranked)
    true_budget_value = sum(true_weights[channel] * true_roi[channel] for channel in true_roi)
    estimated_budget_value = sum(estimated_weights[channel] * true_roi[channel] for channel in true_roi)
    budget_efficiency_ratio = estimated_budget_value / true_budget_value if true_budget_value > 0 else 0.0

    return {
        "true_channel_rank": ">".join(true_ranked),
        "estimated_channel_rank": ">".join(estimated_ranked),
        "true_top_channel": true_ranked[0],
        "estimated_top_channel": estimated_ranked[0],
        "top_channel_recovered": 1 if true_ranked[0] == estimated_ranked[0] else 0,
        "top2_budget_direction_overlap": len(true_top2.intersection(estimated_top2)) / 2.0,
        "spearman_rank_corr": spearman_rank_corr(true_roi, estimated_coefficients),
        "budget_efficiency_ratio": budget_efficiency_ratio,
        "positive_sign_accuracy": sum(1 for value in estimated_coefficients.values() if value > 0) / len(estimated_coefficients),
    }


def run_simulations() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    panel_rows = prepared_panel()
    channels = channel_assumptions()
    channel_names = [str(channel["channel"]) for channel in channels]
    replicate_rows: list[dict[str, object]] = []

    for scenario in scenario_rows():
        replications = to_int(scenario["replications"])
        for replicate in range(1, replications + 1):
            simulated, true_roi = simulate_dataset(panel_rows, channels, scenario, replicate)
            for model_spec in MODEL_SPECS:
                estimated = fit_ridge_coefficients(simulated, channels, model_spec)
                metrics = recovery_metrics(true_roi, estimated)
                replicate_rows.append(
                    {
                        "scenario_id": scenario["scenario_id"],
                        "spend_mechanism": scenario["spend_mechanism"],
                        "effect_strength": scenario["effect_strength"],
                        "effect_multiplier": to_float(scenario["effect_multiplier"]),
                        "noise_pct": to_float(scenario["noise_pct"]),
                        "replicate": replicate,
                        "model_spec": model_spec,
                        **metrics,
                        **{f"coef_{channel}": estimated[channel] for channel in channel_names},
                        **{f"true_roi_{channel}": true_roi[channel] for channel in channel_names},
                    }
                )

    summary_rows = summarize_replicates(replicate_rows)
    return replicate_rows, summary_rows


def summarize_replicates(replicate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in replicate_rows:
        groups[(str(row["scenario_id"]), str(row["model_spec"]))].append(row)

    summary_rows = []
    for (scenario_id, model_spec), rows in sorted(groups.items()):
        first = rows[0]
        n = len(rows)
        summary_rows.append(
            {
                "scenario_id": scenario_id,
                "spend_mechanism": first["spend_mechanism"],
                "effect_strength": first["effect_strength"],
                "effect_multiplier": first["effect_multiplier"],
                "noise_pct": first["noise_pct"],
                "model_spec": model_spec,
                "replications": n,
                "top_channel_recovery_rate": sum(float(row["top_channel_recovered"]) for row in rows) / n,
                "mean_top2_budget_direction_overlap": sum(float(row["top2_budget_direction_overlap"]) for row in rows) / n,
                "mean_spearman_rank_corr": sum(float(row["spearman_rank_corr"]) for row in rows) / n,
                "mean_budget_efficiency_ratio": sum(float(row["budget_efficiency_ratio"]) for row in rows) / n,
                "mean_positive_sign_accuracy": sum(float(row["positive_sign_accuracy"]) for row in rows) / n,
                "dominant_estimated_top_channel": mode([str(row["estimated_top_channel"]) for row in rows]),
            }
        )
    return summary_rows


def mode(values: list[str]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return sorted(counts, key=lambda key: (-counts[key], key))[0]


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            formatted = {}
            for field in fields:
                value = row.get(field, "")
                if isinstance(value, float):
                    formatted[field] = f"{value:.6f}"
                else:
                    formatted[field] = value
            writer.writerow(formatted)


def format_percent(value: object) -> str:
    return f"{float(value):.0%}"


def format_decimal(value: object, digits: int = 2) -> str:
    return f"{float(value):.{digits}f}"


def summary_table(rows: list[dict[str, object]], model_spec: str) -> list[str]:
    filtered = [row for row in rows if row["model_spec"] == model_spec]
    lines = [
        "| Mechanism | Effect | Top channel recovery | Top-2 direction overlap | Rank corr. | Budget efficiency | Dominant estimated top |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in filtered:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["spend_mechanism"]),
                    str(row["effect_strength"]),
                    format_percent(row["top_channel_recovery_rate"]),
                    format_percent(row["mean_top2_budget_direction_overlap"]),
                    format_decimal(row["mean_spearman_rank_corr"]),
                    format_percent(row["mean_budget_efficiency_ratio"]),
                    str(row["dominant_estimated_top_channel"]),
                ]
            )
            + " |"
        )
    return lines


def key_takeaways(rows: list[dict[str, object]]) -> list[str]:
    saturation = [row for row in rows if row["model_spec"] == "controlled_saturation"]
    adstock = [row for row in rows if row["model_spec"] == "controlled_adstock"]
    weak = [row for row in saturation if row["effect_strength"] == "weak"]
    bundle = [row for row in saturation if row["spend_mechanism"] == "channel_bundle"]
    randomized = [row for row in saturation if row["spend_mechanism"] == "randomized"]
    risk = [row for row in saturation if row["spend_mechanism"] == "risk_targeting"]

    def avg(field: str, subset: list[dict[str, object]]) -> float:
        return sum(float(row[field]) for row in subset) / len(subset)

    lines = [
        f"- Controlled/saturation model average budget-efficiency ratio in randomized spend scenarios: {format_percent(avg('mean_budget_efficiency_ratio', randomized))}.",
        f"- Controlled/saturation model average top-2 direction overlap in weak-effect scenarios: {format_percent(avg('mean_top2_budget_direction_overlap', weak))}.",
        f"- Channel-bundle scenarios are the hardest identification setting; controlled/saturation average rank correlation: {format_decimal(avg('mean_spearman_rank_corr', bundle))}.",
        f"- Risk-targeting scenarios test negative confounding; controlled/saturation average budget-efficiency ratio: {format_percent(avg('mean_budget_efficiency_ratio', risk))}.",
        f"- Linear controlled/adstock average top-channel recovery is {format_percent(avg('top_channel_recovery_rate', adstock))}, which is a useful warning that adstock alone is not enough.",
    ]
    return lines


def write_markdown(summary_rows: list[dict[str, object]]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Marketing Sensitivity Analysis V0",
        "",
        "This simulation tests whether marketing models recover the correct channel ranking and budget direction under different simulated marketing data-generating mechanisms.",
        "",
        "This is stricter than the earlier response scenario analysis: it tests model recovery, not only output sensitivity.",
        "",
        "## Key Takeaways",
        "",
    ]
    lines.extend(key_takeaways(summary_rows))
    lines.extend(
        [
            "",
            "## Controlled / Saturation Model",
            "",
        ]
    )
    lines.extend(summary_table(summary_rows, "controlled_saturation"))
    lines.extend(
        [
            "",
            "## Controlled / Adstock Model",
            "",
        ]
    )
    lines.extend(summary_table(summary_rows, "controlled_adstock"))
    lines.extend(
        [
            "",
            "## Naive Raw-Spend Model",
            "",
        ]
    )
    lines.extend(summary_table(summary_rows, "naive_raw_spend"))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `top_channel_recovery_rate` checks whether the model identifies the true strongest channel.",
            "- `top2_budget_direction_overlap` checks whether the model points budget toward the correct top channels.",
            "- `budget_efficiency_ratio` compares the true value of the model-implied channel budget direction with the true optimal direction.",
            "- Low recovery in bundled or weak-effect scenarios means channel-level ranking should be treated as fragile, even if route-level budget recommendations remain useful.",
        ]
    )
    SUMMARY_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(summary_rows: list[dict[str, object]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    saturation = [row for row in summary_rows if row["model_spec"] == "controlled_saturation"]
    controlled = [row for row in summary_rows if row["model_spec"] == "controlled_adstock"]
    naive = [row for row in summary_rows if row["model_spec"] == "naive_raw_spend"]

    def avg(field: str, subset: list[dict[str, object]]) -> float:
        return sum(float(row[field]) for row in subset) / len(subset)

    lines = [
        "# Phase 4B Memo: Marketing Sensitivity and Recovery Analysis V0",
        "",
        "## Business Question",
        "",
        "If marketing data is simulated, under what conditions can a marketing model recover the correct channel ranking and budget direction?",
        "",
        "## Why This Matters",
        "",
        "The project should not claim that simulated marketing spend proves true MMM performance. Instead, the useful question is whether the modeling workflow is robust under plausible data-generating mechanisms.",
        "",
        "## Simulation Design",
        "",
        "The sensitivity layer varies two dimensions:",
        "",
        "- Marketing spend generation: randomized, demand-following, risk-targeting, seasonal campaign, and bundled-channel spend.",
        "- True effect strength: weak, base, and strong.",
        "",
        "Each scenario is run for 40 deterministic replications and evaluated with three model specs:",
        "",
        "- `naive_raw_spend`: raw spend without controls.",
        "- `controlled_adstock`: adstocked spend with route and month controls.",
        "- `controlled_saturation`: an MMM-like response transformation with adstock, saturation, route controls, and month controls.",
        "",
        "## High-Level Result",
        "",
        f"- Controlled/saturation average top-channel recovery: {format_percent(avg('top_channel_recovery_rate', saturation))}.",
        f"- Controlled/adstock average top-channel recovery: {format_percent(avg('top_channel_recovery_rate', controlled))}.",
        f"- Naive raw-spend average top-channel recovery: {format_percent(avg('top_channel_recovery_rate', naive))}.",
        f"- Controlled/saturation average budget-efficiency ratio: {format_percent(avg('mean_budget_efficiency_ratio', saturation))}.",
        f"- Controlled/adstock average budget-efficiency ratio: {format_percent(avg('mean_budget_efficiency_ratio', controlled))}.",
        f"- Naive raw-spend average budget-efficiency ratio: {format_percent(avg('mean_budget_efficiency_ratio', naive))}.",
        "",
        "## Interpretation",
        "",
        "If effects are weak or channels are bought as a tight bundle, channel-level ranking becomes fragile. In those cases, the project should emphasize route-level budget direction, experiment design, and grouped-channel guardrails rather than precise channel rank claims.",
        "",
        "The recovery results show that exogenous spend variation alone is not enough in a small, noisy panel. Channel ranking becomes more credible only when true effects are strong enough, channels are not tightly bundled, outcomes are measured cleanly, and the model includes adstock/saturation structure. That supports the project framing: Meridian or any MMM component should be used as a measurement module only when real spend variation and outcomes are strong enough.",
        "",
        "## Next Step",
        "",
        "Use this sensitivity layer in the portfolio package as the evidence that the project understands simulated marketing limitations and validates model recovery before claiming optimization value.",
    ]
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    replicate_rows, summary_rows = run_simulations()

    channel_names = [str(channel["channel"]) for channel in channel_assumptions()]
    replicate_fields = [
        "scenario_id",
        "spend_mechanism",
        "effect_strength",
        "effect_multiplier",
        "noise_pct",
        "replicate",
        "model_spec",
        "true_channel_rank",
        "estimated_channel_rank",
        "true_top_channel",
        "estimated_top_channel",
        "top_channel_recovered",
        "top2_budget_direction_overlap",
        "spearman_rank_corr",
        "budget_efficiency_ratio",
        "positive_sign_accuracy",
    ]
    replicate_fields.extend([f"coef_{channel}" for channel in channel_names])
    replicate_fields.extend([f"true_roi_{channel}" for channel in channel_names])

    summary_fields = [
        "scenario_id",
        "spend_mechanism",
        "effect_strength",
        "effect_multiplier",
        "noise_pct",
        "model_spec",
        "replications",
        "top_channel_recovery_rate",
        "mean_top2_budget_direction_overlap",
        "mean_spearman_rank_corr",
        "mean_budget_efficiency_ratio",
        "mean_positive_sign_accuracy",
        "dominant_estimated_top_channel",
    ]

    write_rows(REPLICATE_FILE, replicate_rows, replicate_fields)
    write_rows(SUMMARY_CSV_FILE, summary_rows, summary_fields)
    write_markdown(summary_rows)
    write_report(summary_rows)

    print(f"Wrote {REPLICATE_FILE}")
    print(f"Wrote {SUMMARY_CSV_FILE}")
    print(f"Wrote {SUMMARY_MD_FILE}")
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
