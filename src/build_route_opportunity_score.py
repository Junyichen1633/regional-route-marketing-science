"""Build a route-level opportunity score from the route-month panel.

This is a transparent v0 decision layer. It is intentionally heuristic: the goal
is to turn the current public-data panel into an interpretable route ranking
before adding marketing response curves and budget optimization.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import median


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"

PANEL_FILE = PROCESSED_DIR / "route_month_panel_v2.csv"
SCORE_FILE = PROCESSED_DIR / "route_opportunity_score_v0.csv"
SUMMARY_FILE = OUTPUTS_DIR / "route_opportunity_score_v0_summary.md"
REPORT_FILE = REPORTS_DIR / "phase3_route_opportunity_memo.md"

ANALYSIS_START_YEAR = 2023
ANALYSIS_END_YEAR = 2025
RECENT_YEAR = 2025
FREQUENCY_SCORE_CAP_WEEKLY_FLIGHTS = 14.0

CONFIDENCE_WEIGHTS = {
    "high": 1.00,
    "medium": 0.75,
    "low": 0.50,
    "assumption": 0.45,
    "synthetic": 0.35,
    "uncovered": 0.00,
    "": 0.00,
}


def read_panel() -> list[dict[str, str]]:
    with PANEL_FILE.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_int(value: str | None) -> int | None:
    numeric = to_float(value)
    if numeric is None:
        return None
    return int(numeric)


def first_non_empty(rows: list[dict[str, str]], field: str) -> str:
    for row in rows:
        value = row.get(field, "")
        if value != "":
            return value
    return ""


def mean_value(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def median_value(values: list[float | None]) -> float | None:
    clean = sorted(value for value in values if value is not None)
    if not clean:
        return None
    return float(median(clean))


def active_rate(rows: list[dict[str, str]]) -> float | None:
    labeled = [row for row in rows if row.get("route_active") in {"0", "1"}]
    if not labeled:
        return None
    active = sum(1 for row in labeled if row.get("route_active") == "1")
    return active / len(labeled)


def last_labeled_status(rows: list[dict[str, str]]) -> tuple[str, str]:
    labeled = [row for row in rows if row.get("route_active") in {"0", "1"}]
    if not labeled:
        return "", "unlabeled"
    last_row = sorted(labeled, key=lambda row: row.get("month", ""))[-1]
    return last_row.get("month", ""), "active" if last_row.get("route_active") == "1" else "inactive"


def confidence_weight(value: str) -> float:
    parts = [part.strip().lower() for part in value.replace("|", ";").split(";") if part.strip()]
    if not parts:
        return 0.0
    return max(CONFIDENCE_WEIGHTS.get(part, 0.35) for part in parts)


def clamp_score(value: float) -> float:
    return min(100.0, max(0.0, value))


def log1p(value: float | None) -> float:
    if value is None:
        return 0.0
    return math.log1p(max(0.0, value))


def minmax_scores(records: list[dict[str, object]], field: str) -> dict[str, float]:
    values = [float(record[field]) for record in records]
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        return {str(record["route_id"]): 50.0 for record in records}
    return {
        str(record["route_id"]): ((float(record[field]) - low) / (high - low)) * 100.0
        for record in records
    }


def model_role(route_group: str, strategic_role: str, route_id: str) -> str:
    if route_group == "hub_to_hub":
        return "benchmark"
    if strategic_role == "local_competition" or route_id == "YXX_YVR":
        return "negative_control"
    return "target"


def strategic_fit_score(route_group: str, strategic_role: str, route_segment: str, role: str) -> float:
    if role == "negative_control":
        return 0.0
    if role == "benchmark":
        return 25.0
    if strategic_role == "long_haul_regional":
        return 100.0
    if strategic_role in {"western_access", "eastern_access"} and route_segment == "long_haul":
        return 92.0
    if strategic_role in {"western_access", "eastern_access", "bc_connectivity"}:
        return 78.0
    if route_group == "regional_to_hub":
        return 72.0
    return 55.0


def recommendation(record: dict[str, object]) -> str:
    role = str(record["model_role"])
    end_status = str(record["end_of_period_route_status"])
    priority = float(record["marketing_support_priority_score_v0"])
    sustainability = float(record["route_sustainability_score_v0"])
    data_confidence = float(record["data_confidence_score"])

    if role == "benchmark":
        return "Benchmark only; exclude from regional marketing allocation"
    if role == "negative_control":
        return "Control route; do not prioritize"
    if data_confidence < 45:
        return "Needs schedule data before spend decision"
    if end_status == "inactive" and priority >= 60:
        return "Relaunch feasibility test; verify airline capacity first"
    if end_status == "inactive":
        return "Currently inactive; monitor before marketing allocation"
    if priority >= 70 and sustainability >= 55:
        return "Scale or defend with controlled campaign"
    if priority >= 60:
        return "Run test-and-learn marketing"
    if sustainability >= 70:
        return "Maintain service; monitor capacity and leakage"
    if priority >= 45:
        return "Watchlist; improve evidence first"
    return "Low priority for marketing allocation"


def build_base_records(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_route: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_route[row["route_id"]].append(row)

    records: list[dict[str, object]] = []
    for route_id in sorted(by_route):
        route_rows = by_route[route_id]
        period_rows = [
            row
            for row in route_rows
            if ANALYSIS_START_YEAR <= (to_int(row.get("year")) or 0) <= ANALYSIS_END_YEAR
        ]
        recent_rows = [row for row in period_rows if to_int(row.get("year")) == RECENT_YEAR]
        labeled_period = [row for row in period_rows if row.get("route_active") in {"0", "1"}]
        active_period = [row for row in labeled_period if row.get("route_active") == "1"]

        route_group = first_non_empty(route_rows, "route_group")
        strategic_role = first_non_empty(route_rows, "strategic_role")
        route_segment = first_non_empty(route_rows, "route_segment")
        role = model_role(route_group, strategic_role, route_id)

        total_period_months = len(period_rows)
        labeled_months = len(labeled_period)
        active_months = len(active_period)
        inactive_months = sum(1 for row in labeled_period if row.get("route_active") == "0")
        uncovered_months = total_period_months - labeled_months
        label_coverage = labeled_months / total_period_months if total_period_months else 0.0

        period_active_rate = active_rate(period_rows)
        recent_active_rate = active_rate(recent_rows)
        last_labeled_month, end_status = last_labeled_status(period_rows)
        end_status_score = 100.0 if end_status == "active" else 15.0 if end_status == "inactive" else 0.0
        active_rate_for_scoring = (
            recent_active_rate
            if recent_active_rate is not None
            else period_active_rate
            if period_active_rate is not None
            else 0.0
        )

        frequency_proxy = median_value(
            [to_float(row.get("direct_weekly_frequency_proxy")) for row in active_period]
        )
        frequency_for_scoring = frequency_proxy or 0.0
        frequency_score = clamp_score((frequency_for_scoring / FREQUENCY_SCORE_CAP_WEEKLY_FLIGHTS) * 100.0)

        avg_origin_movements = mean_value(
            [to_float(row.get("origin_domestic_air_carrier_all_levels_movements")) for row in period_rows]
        )
        avg_destination_movements = mean_value(
            [to_float(row.get("destination_domestic_air_carrier_all_levels_movements")) for row in period_rows]
        )
        avg_nearest_hub_movements = mean_value(
            [to_float(row.get("nearest_origin_hub_domestic_air_carrier_all_levels_movements")) for row in period_rows]
        )
        avg_destination_screened = mean_value(
            [to_float(row.get("destination_monthly_screened_passengers")) for row in period_rows]
        )
        avg_nearest_hub_screened = mean_value(
            [to_float(row.get("nearest_origin_hub_monthly_screened_passengers")) for row in period_rows]
        )

        hub_distance = to_float(first_non_empty(route_rows, "nearest_origin_hub_distance_km")) or 0.0
        competition_pressure_raw = (avg_nearest_hub_movements or 0.0) / max(hub_distance, 25.0)
        confidence = mean_value([confidence_weight(row.get("route_supply_confidence", "")) for row in period_rows]) or 0.0
        data_confidence = clamp_score((0.75 * label_coverage + 0.25 * confidence) * 100.0)

        service_viability = clamp_score(
            (0.35 * end_status_score)
            + (0.25 * active_rate_for_scoring * 100.0)
            + (0.20 * (period_active_rate or 0.0) * 100.0)
            + (0.15 * frequency_score)
            + (0.10 * label_coverage * 100.0)
        )

        if role != "target":
            service_gap = 0.0
        elif end_status == "inactive" and (period_active_rate or 0.0) >= 0.50:
            service_gap = 75.0
        elif active_rate_for_scoring >= 0.50:
            service_gap = clamp_score(100.0 - frequency_score)
        elif (period_active_rate or 0.0) >= 0.25:
            service_gap = 55.0
        else:
            service_gap = 15.0

        records.append(
            {
                "route_id": route_id,
                "model_role": role,
                "origin_iata": first_non_empty(route_rows, "origin_iata"),
                "destination_iata": first_non_empty(route_rows, "destination_iata"),
                "route_group": route_group,
                "strategic_role": strategic_role,
                "route_segment": route_segment,
                "distance_km": to_float(first_non_empty(route_rows, "distance_km")),
                "nearest_origin_hub_iata": first_non_empty(route_rows, "nearest_origin_hub_iata"),
                "nearest_origin_hub_distance_km": hub_distance,
                "total_months_2023_2025": total_period_months,
                "labeled_months_2023_2025": labeled_months,
                "active_months_2023_2025": active_months,
                "inactive_months_2023_2025": inactive_months,
                "uncovered_months_2023_2025": uncovered_months,
                "label_coverage_2023_2025": label_coverage,
                "active_rate_2023_2025": period_active_rate,
                "recent_active_rate_2025": recent_active_rate,
                "last_labeled_month_2023_2025": last_labeled_month,
                "end_of_period_route_status": end_status,
                "median_weekly_frequency_proxy_2023_2025": frequency_proxy,
                "frequency_score": frequency_score,
                "avg_origin_domestic_air_carrier_movements_2023_2025": avg_origin_movements,
                "avg_destination_domestic_air_carrier_movements_2023_2025": avg_destination_movements,
                "avg_nearest_hub_domestic_air_carrier_movements_2023_2025": avg_nearest_hub_movements,
                "avg_destination_screened_passengers_2023_2025": avg_destination_screened,
                "avg_nearest_hub_screened_passengers_2023_2025": avg_nearest_hub_screened,
                "competition_pressure_raw": competition_pressure_raw,
                "regional_strategic_fit_score": strategic_fit_score(
                    route_group, strategic_role, route_segment, role
                ),
                "service_viability_score": service_viability,
                "service_gap_score": service_gap,
                "data_confidence_score": data_confidence,
                "log_origin_movements": log1p(avg_origin_movements),
                "log_destination_movements": log1p(avg_destination_movements),
                "log_destination_screened": log1p(avg_destination_screened),
                "log_nearest_hub_screened": log1p(avg_nearest_hub_screened),
                "log_competition_pressure": log1p(competition_pressure_raw),
            }
        )
    return records


def add_scores(records: list[dict[str, object]]) -> list[dict[str, object]]:
    origin_scores = minmax_scores(records, "log_origin_movements")
    destination_movement_scores = minmax_scores(records, "log_destination_movements")
    destination_screened_scores = minmax_scores(records, "log_destination_screened")
    hub_screened_scores = minmax_scores(records, "log_nearest_hub_screened")
    competition_scores = minmax_scores(records, "log_competition_pressure")

    for record in records:
        route_id = str(record["route_id"])
        demand_context = (
            0.35 * origin_scores[route_id]
            + 0.30 * destination_movement_scores[route_id]
            + 0.25 * destination_screened_scores[route_id]
            + 0.10 * hub_screened_scores[route_id]
        )
        competition = competition_scores[route_id]
        sustainability = (
            0.35 * float(record["service_viability_score"])
            + 0.30 * demand_context
            + 0.20 * float(record["regional_strategic_fit_score"])
            + 0.15 * float(record["data_confidence_score"])
            - 0.10 * competition
        )

        if record["model_role"] == "target":
            priority = (
                0.30 * demand_context
                + 0.25 * float(record["regional_strategic_fit_score"])
                + 0.20 * competition
                + 0.15 * float(record["service_gap_score"])
                + 0.10 * float(record["data_confidence_score"])
            )
            if float(record["data_confidence_score"]) < 45.0:
                priority *= 0.75
        else:
            priority = 0.0

        record["demand_context_score"] = clamp_score(demand_context)
        record["competition_pressure_score"] = clamp_score(competition)
        record["route_sustainability_score_v0"] = clamp_score(sustainability)
        record["marketing_support_priority_score_v0"] = clamp_score(priority)
        record["recommendation"] = recommendation(record)

    ranked_targets = sorted(
        [record for record in records if record["model_role"] == "target"],
        key=lambda record: (
            -float(record["marketing_support_priority_score_v0"]),
            -float(record["route_sustainability_score_v0"]),
            str(record["route_id"]),
        ),
    )
    for rank, record in enumerate(ranked_targets, start=1):
        record["opportunity_rank_target_only"] = rank
    for record in records:
        record.setdefault("opportunity_rank_target_only", "")

    return sorted(
        records,
        key=lambda record: (
            str(record["model_role"]) != "target",
            record.get("opportunity_rank_target_only") if record.get("opportunity_rank_target_only") != "" else 999,
            str(record["route_id"]),
        ),
    )


def format_decimal(value: object, digits: int = 2) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.{digits}f}"


def format_percent(value: object) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.1%}"


def write_csv(records: list[dict[str, object]]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    fields = [
        "route_id",
        "model_role",
        "origin_iata",
        "destination_iata",
        "route_group",
        "strategic_role",
        "route_segment",
        "distance_km",
        "nearest_origin_hub_iata",
        "nearest_origin_hub_distance_km",
        "total_months_2023_2025",
        "labeled_months_2023_2025",
        "active_months_2023_2025",
        "inactive_months_2023_2025",
        "uncovered_months_2023_2025",
        "label_coverage_2023_2025",
        "active_rate_2023_2025",
        "recent_active_rate_2025",
        "last_labeled_month_2023_2025",
        "end_of_period_route_status",
        "median_weekly_frequency_proxy_2023_2025",
        "avg_origin_domestic_air_carrier_movements_2023_2025",
        "avg_destination_domestic_air_carrier_movements_2023_2025",
        "avg_nearest_hub_domestic_air_carrier_movements_2023_2025",
        "avg_destination_screened_passengers_2023_2025",
        "competition_pressure_score",
        "demand_context_score",
        "service_viability_score",
        "regional_strategic_fit_score",
        "service_gap_score",
        "data_confidence_score",
        "route_sustainability_score_v0",
        "marketing_support_priority_score_v0",
        "opportunity_rank_target_only",
        "recommendation",
    ]

    with SCORE_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            output_record: dict[str, object] = {}
            for field in fields:
                value = record.get(field, "")
                if isinstance(value, float):
                    output_record[field] = f"{value:.4f}"
                else:
                    output_record[field] = value
            writer.writerow(output_record)


def markdown_table(records: list[dict[str, object]], limit: int | None = None) -> list[str]:
    table_records = records if limit is None else records[:limit]
    lines = [
        "| Rank | Route | End status | Priority | Sustainability | Active rate 2023-2025 | Data confidence | Recommendation |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for record in table_records:
        rank = record.get("opportunity_rank_target_only", "")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    str(record["route_id"]),
                    str(record["end_of_period_route_status"]),
                    format_decimal(record["marketing_support_priority_score_v0"], 1),
                    format_decimal(record["route_sustainability_score_v0"], 1),
                    format_percent(record["active_rate_2023_2025"]),
                    format_decimal(record["data_confidence_score"], 1),
                    str(record["recommendation"]),
                ]
            )
            + " |"
        )
    return lines


def write_summary(records: list[dict[str, object]]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    targets = [record for record in records if record["model_role"] == "target"]
    benchmarks = [record for record in records if record["model_role"] == "benchmark"]
    controls = [record for record in records if record["model_role"] == "negative_control"]

    lines = [
        "# Route Opportunity Score V0",
        "",
        "This file summarizes a transparent route-level scoring layer built from `route_month_panel_v2.csv`.",
        "",
        "The score is a decision-support baseline, not a causal MMM estimate.",
        "",
        "## Scope",
        "",
        f"- Analysis window: {ANALYSIS_START_YEAR}-{ANALYSIS_END_YEAR}",
        f"- Routes scored: {len(records)}",
        f"- Target regional routes: {len(targets)}",
        f"- Benchmark routes: {len(benchmarks)}",
        f"- Negative/control routes: {len(controls)}",
        "",
        "## Score Components",
        "",
        "- `service_viability_score`: route-active continuity, recent 2025 activity, frequency proxy, and label coverage.",
        "- `demand_context_score`: origin airport movement scale, destination movement scale, destination screened passengers, and nearby hub demand context.",
        "- `regional_strategic_fit_score`: business fit for regional airport support, with hub-to-hub routes treated as benchmarks.",
        "- `competition_pressure_score`: nearby hub activity adjusted by distance from the origin airport.",
        "- `data_confidence_score`: route label coverage plus source confidence.",
        "",
        "## Top Target Routes by Marketing Support Priority",
        "",
    ]
    lines.extend(markdown_table(targets, limit=10))
    lines.extend(
        [
            "",
            "## Benchmarks and Controls",
            "",
        ]
    )
    lines.extend(markdown_table(benchmarks + controls))
    lines.extend(
        [
            "",
            "## Formula Notes",
            "",
            "`route_sustainability_score_v0` rewards end-of-period service status, recent activity, demand context, strategic fit, and data confidence, then penalizes nearby hub competition pressure.",
            "",
            "`marketing_support_priority_score_v0` is only assigned to target regional routes. It rewards demand context, strategic fit, hub-leakage pressure, service gaps, and data confidence.",
            "",
            "Because route-level passenger demand and true marketing spend are not observed yet, these scores should be interpreted as a portfolio triage tool.",
        ]
    )
    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(records: list[dict[str, object]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    targets = [record for record in records if record["model_role"] == "target"]
    top_targets = targets[:5]

    lines = [
        "# Phase 3 Memo: Route Opportunity Score V0",
        "",
        "## Business Question",
        "",
        "Which regional Canadian air routes look most worth supporting with marketing, given public airport activity data, sourced route supply signals, and nearby hub competition?",
        "",
        "## Current Answer",
        "",
        "The v0 score produces a target-route ranking that separates three ideas:",
        "",
        "- Sustainability: whether the route appears operationally viable before marketing.",
        "- Marketing support priority: whether limited budget should be tested or defended on the route.",
        "- Evidence quality: whether the decision has enough sourced schedule coverage to be credible.",
        "",
        "## Top Target Routes",
        "",
    ]
    lines.extend(markdown_table(top_targets))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "High priority routes are not automatically the largest routes. They are routes where regional strategic value, demand context, hub leakage pressure, service gaps, and evidence quality line up.",
            "",
            "Hub-to-hub routes are retained as benchmarks, not as candidates for regional marketing allocation. The local YXX-YVR route is retained as a negative/control route because its value proposition is structurally different from longer regional-to-hub access routes.",
            "",
            "## Limitations",
            "",
            "- No route-month passenger demand is observed yet.",
            "- `direct_weekly_frequency_proxy` is event-based and incomplete.",
            "- The score is heuristic, so it should be challenged with sensitivity analysis.",
            "- Marketing effects are not estimated in this phase.",
            "",
            "## Next Step",
            "",
            "Build a marketing response scenario module that converts budget into incremental passenger or route-health lift under conservative, base, and optimistic assumptions.",
        ]
    )
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = read_panel()
    if not rows:
        raise ValueError(f"No rows found in {PANEL_FILE}")
    records = add_scores(build_base_records(rows))
    write_csv(records)
    write_summary(records)
    write_report(records)
    print(f"Wrote {SCORE_FILE}")
    print(f"Wrote {SUMMARY_FILE}")
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
