"""Build scenario-based marketing response curves for candidate routes.

This module does not estimate causal MMM. It uses transparent assumptions to
translate route opportunity scores into conservative/base/optimistic response
curves that can feed the next budget optimization layer.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"

SCORE_FILE = PROCESSED_DIR / "route_opportunity_score_v0.csv"
ASSUMPTIONS_FILE = CONFIG_DIR / "marketing_response_assumptions.csv"
CURVE_FILE = PROCESSED_DIR / "marketing_response_curve_v0.csv"
ROUTE_SUMMARY_FILE = PROCESSED_DIR / "marketing_response_route_summary_v0.csv"
SUMMARY_FILE = OUTPUTS_DIR / "marketing_response_scenarios_v0_summary.md"
REPORT_FILE = REPORTS_DIR / "phase4_marketing_response_memo.md"

BUDGET_GRID_CAD = [0, 25_000, 50_000, 75_000, 100_000, 150_000, 250_000, 400_000]

SEATS_BY_SEGMENT = {
    "short_haul": 78,
    "medium_haul": 132,
    "long_haul": 186,
}

DEFAULT_WEEKLY_FREQUENCY = {
    "short_haul": 7.0,
    "medium_haul": 4.0,
    "long_haul": 3.0,
}

BASE_LOAD_FACTOR = 0.78


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


def assumption_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        lookup[(row["scenario"], row["route_segment"])] = row
    return lookup


def route_frequency(record: dict[str, str]) -> float:
    segment = record["route_segment"]
    observed = to_float(record.get("median_weekly_frequency_proxy_2023_2025"))
    if observed > 0:
        return observed
    return DEFAULT_WEEKLY_FREQUENCY.get(segment, 4.0)


def annual_passenger_proxy(record: dict[str, str]) -> float:
    """Return a capacity-and-demand scaled annual passenger proxy.

    The unit is proxy passengers, not observed passengers. It starts from a
    simple two-way seat capacity approximation and scales it by demand context.
    """

    segment = record["route_segment"]
    weekly_frequency = route_frequency(record)
    seats = SEATS_BY_SEGMENT.get(segment, 132)
    capacity_proxy = weekly_frequency * 52 * 2 * seats * BASE_LOAD_FACTOR

    demand_context = to_float(record.get("demand_context_score"))
    demand_multiplier = 0.65 + 0.70 * (demand_context / 100.0)

    end_status = record.get("end_of_period_route_status", "")
    status_multiplier = 0.70 if end_status == "inactive" else 1.0

    data_confidence = to_float(record.get("data_confidence_score"))
    confidence_multiplier = 0.85 + 0.15 * (data_confidence / 100.0)

    return capacity_proxy * demand_multiplier * status_multiplier * confidence_multiplier


def adjusted_max_lift_pct(record: dict[str, str], assumption: dict[str, str]) -> float:
    base_lift = to_float(assumption["max_lift_pct"])
    priority = to_float(record.get("marketing_support_priority_score_v0"))
    data_confidence = to_float(record.get("data_confidence_score"))
    end_status = record.get("end_of_period_route_status", "")

    priority_multiplier = 0.75 + 0.50 * (priority / 100.0)
    confidence_multiplier = 0.70 + 0.30 * (data_confidence / 100.0)
    inactive_multiplier = 0.70 if end_status == "inactive" else 1.0

    return base_lift * priority_multiplier * confidence_multiplier * inactive_multiplier


def adjusted_half_saturation(record: dict[str, str], assumption: dict[str, str]) -> float:
    half_saturation = to_float(assumption["half_saturation_spend_cad"])
    data_confidence = to_float(record.get("data_confidence_score"))
    end_status = record.get("end_of_period_route_status", "")

    if end_status == "inactive":
        half_saturation *= 1.35
    if data_confidence < 60:
        half_saturation *= 1.20
    return half_saturation


def response_share(budget_cad: float, half_saturation_cad: float) -> float:
    if budget_cad <= 0:
        return 0.0
    return budget_cad / (budget_cad + half_saturation_cad)


def health_lift_points(record: dict[str, str], share: float, scenario: str, incremental_pct: float) -> float:
    priority = to_float(record.get("marketing_support_priority_score_v0"))
    service_gap = to_float(record.get("service_gap_score"))
    scenario_multiplier = {"conservative": 0.75, "base": 1.00, "optimistic": 1.25}[scenario]
    lift = share * (1.5 + 0.045 * priority + 0.035 * service_gap) * scenario_multiplier
    lift += incremental_pct * 100.0 * 0.35
    return min(12.0, max(0.0, lift))


def route_test_budget(record: dict[str, str]) -> int:
    priority = to_float(record.get("marketing_support_priority_score_v0"))
    data_confidence = to_float(record.get("data_confidence_score"))
    recommendation = record.get("recommendation", "")
    end_status = record.get("end_of_period_route_status", "")

    if data_confidence < 45:
        return 25_000
    if end_status == "inactive":
        return 75_000
    if "Scale or defend" in recommendation or priority >= 70:
        return 150_000
    if "Run test" in recommendation or priority >= 60:
        return 100_000
    if "Maintain" in recommendation:
        return 50_000
    return 25_000


def build_curves(
    score_rows: list[dict[str, str]], assumptions: dict[tuple[str, str], dict[str, str]]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    target_rows = [row for row in score_rows if row.get("model_role") == "target"]
    curve_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for record in target_rows:
        route_id = record["route_id"]
        segment = record["route_segment"]
        baseline_proxy = annual_passenger_proxy(record)
        selected_budget = route_test_budget(record)

        for scenario in ["conservative", "base", "optimistic"]:
            assumption = assumptions[(scenario, segment)]
            max_lift = adjusted_max_lift_pct(record, assumption)
            half_saturation = adjusted_half_saturation(record, assumption)
            carryover = to_float(assumption["adstock_carryover_multiplier"], default=1.0)
            selected_row: dict[str, object] | None = None

            for budget in BUDGET_GRID_CAD:
                share = response_share(float(budget), half_saturation)
                incremental_proxy = baseline_proxy * max_lift * share * carryover
                incremental_pct = incremental_proxy / baseline_proxy if baseline_proxy else 0.0
                cost_per_incremental = (
                    float(budget) / incremental_proxy if budget > 0 and incremental_proxy > 0 else None
                )
                health_lift = health_lift_points(record, share, scenario, incremental_pct)
                row = {
                    "route_id": route_id,
                    "scenario": scenario,
                    "campaign_budget_cad": budget,
                    "route_segment": segment,
                    "end_of_period_route_status": record.get("end_of_period_route_status", ""),
                    "capacity_required_flag": 1 if record.get("end_of_period_route_status") == "inactive" else 0,
                    "baseline_annual_passenger_proxy": baseline_proxy,
                    "max_lift_pct_adjusted": max_lift,
                    "half_saturation_spend_cad_adjusted": half_saturation,
                    "response_share": share,
                    "incremental_passenger_proxy": incremental_proxy,
                    "incremental_pct_of_baseline_proxy": incremental_pct,
                    "cost_per_incremental_passenger_proxy_cad": cost_per_incremental,
                    "incremental_route_health_points": health_lift,
                    "marketing_support_priority_score_v0": to_float(record.get("marketing_support_priority_score_v0")),
                    "route_sustainability_score_v0": to_float(record.get("route_sustainability_score_v0")),
                    "data_confidence_score": to_float(record.get("data_confidence_score")),
                    "source_recommendation": record.get("recommendation", ""),
                }
                curve_rows.append(row)
                if budget == selected_budget:
                    selected_row = row

            if selected_row is None:
                raise ValueError(f"Selected budget {selected_budget} is not in the grid.")
            summary_rows.append(
                {
                    **selected_row,
                    "selected_test_budget_cad": selected_budget,
                    "scenario_note": assumption["notes"],
                }
            )

    return curve_rows, summary_rows


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            formatted = {}
            for field in fields:
                value = row.get(field, "")
                if value is None:
                    formatted[field] = ""
                elif isinstance(value, float):
                    formatted[field] = f"{value:.4f}"
                else:
                    formatted[field] = value
            writer.writerow(formatted)


def format_money(value: object) -> str:
    if value is None or value == "":
        return ""
    return f"${float(value):,.0f}"


def format_number(value: object, digits: int = 0) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):,.{digits}f}"


def format_decimal(value: object, digits: int = 1) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.{digits}f}"


def markdown_response_table(rows: list[dict[str, object]], limit: int | None = None) -> list[str]:
    shown = rows if limit is None else rows[:limit]
    lines = [
        "| Route | Status | Budget | Incremental passenger proxy | Cost / incr. proxy passenger | Health lift pts | Source recommendation |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in shown:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["route_id"]),
                    str(row["end_of_period_route_status"]),
                    format_money(row["selected_test_budget_cad"]),
                    format_number(row["incremental_passenger_proxy"]),
                    format_money(row["cost_per_incremental_passenger_proxy_cad"]),
                    format_decimal(row["incremental_route_health_points"], 1),
                    str(row["source_recommendation"]),
                ]
            )
            + " |"
        )
    return lines


def write_summary(curve_rows: list[dict[str, object]], summary_rows: list[dict[str, object]]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    base_rows = sorted(
        [row for row in summary_rows if row["scenario"] == "base"],
        key=lambda row: (
            -float(row["incremental_route_health_points"]),
            float(row["cost_per_incremental_passenger_proxy_cad"] or 999999),
        ),
    )

    by_scenario: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in summary_rows:
        by_scenario[str(row["scenario"])].append(row)

    lines = [
        "# Marketing Response Scenarios V0",
        "",
        "This module converts route opportunity scores into scenario-based response curves.",
        "",
        "It is not a causal MMM estimate. It is a transparent simulation layer for budget-planning practice.",
        "",
        "## Generated Assets",
        "",
        f"- Curve rows: {len(curve_rows):,}",
        f"- Route-scenario summary rows: {len(summary_rows):,}",
        "- Budget unit: CAD",
        "- Response horizon: one annual campaign period",
        "",
        "## Top Base-Scenario Route Tests",
        "",
    ]
    lines.extend(markdown_response_table(base_rows, limit=10))
    lines.extend(
        [
            "",
            "## Scenario Totals at Selected Test Budgets",
            "",
            "| Scenario | Selected budget total | Incremental passenger proxy | Mean health lift pts |",
            "|---|---:|---:|---:|",
        ]
    )
    for scenario in ["conservative", "base", "optimistic"]:
        rows = by_scenario[scenario]
        total_budget = sum(float(row["selected_test_budget_cad"]) for row in rows)
        total_incremental = sum(float(row["incremental_passenger_proxy"]) for row in rows)
        mean_health = sum(float(row["incremental_route_health_points"]) for row in rows) / len(rows)
        lines.append(
            f"| {scenario} | {format_money(total_budget)} | {format_number(total_incremental)} | {format_decimal(mean_health, 1)} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Rules",
            "",
            "- For active routes, incremental passenger proxy can be interpreted as demand lift under the stated assumptions.",
            "- For inactive routes, incremental passenger proxy is conditional on service being restorable; marketing cannot create passengers without airline capacity.",
            "- Cost per incremental proxy passenger is useful for comparing routes, not for claiming actual CAC.",
            "- These curves are designed to feed Phase 5 budget optimization.",
        ]
    )
    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(summary_rows: list[dict[str, object]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    base_rows = sorted(
        [row for row in summary_rows if row["scenario"] == "base"],
        key=lambda row: (
            -float(row["incremental_route_health_points"]),
            float(row["cost_per_incremental_passenger_proxy_cad"] or 999999),
        ),
    )

    lines = [
        "# Phase 4 Memo: Marketing Response Scenarios V0",
        "",
        "## Business Question",
        "",
        "If a regional airport had limited marketing funds, how much incremental route demand might different candidate routes generate under conservative, base, and optimistic response assumptions?",
        "",
        "## Method",
        "",
        "This phase uses a diminishing-return response curve rather than a fitted MMM:",
        "",
        "```text",
        "incremental passenger proxy = baseline annual passenger proxy",
        "  x adjusted max lift %",
        "  x budget / (budget + half-saturation spend)",
        "  x scenario carryover multiplier",
        "```",
        "",
        "The baseline passenger proxy is capacity-and-demand scaled. It starts from route frequency, aircraft-seat assumptions, and load factor, then adjusts for demand context, route status, and evidence confidence.",
        "",
        "## Base Scenario Readout",
        "",
    ]
    lines.extend(markdown_response_table(base_rows, limit=8))
    lines.extend(
        [
            "",
            "## Key Caveat",
            "",
            "Inactive-route rows are relaunch scenarios. Their response is conditional on restored airline capacity, so they should be treated as feasibility-test candidates rather than normal media-allocation candidates.",
            "",
            "## Next Step",
            "",
            "Use the response curve table to build a constrained budget optimizer that selects route-budget pairs under a fixed total budget.",
        ]
    )
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    score_rows = read_csv(SCORE_FILE)
    assumption_rows = read_csv(ASSUMPTIONS_FILE)
    assumptions = assumption_lookup(assumption_rows)

    curve_rows, summary_rows = build_curves(score_rows, assumptions)

    curve_fields = [
        "route_id",
        "scenario",
        "campaign_budget_cad",
        "route_segment",
        "end_of_period_route_status",
        "capacity_required_flag",
        "baseline_annual_passenger_proxy",
        "max_lift_pct_adjusted",
        "half_saturation_spend_cad_adjusted",
        "response_share",
        "incremental_passenger_proxy",
        "incremental_pct_of_baseline_proxy",
        "cost_per_incremental_passenger_proxy_cad",
        "incremental_route_health_points",
        "marketing_support_priority_score_v0",
        "route_sustainability_score_v0",
        "data_confidence_score",
        "source_recommendation",
    ]
    summary_fields = curve_fields + ["selected_test_budget_cad", "scenario_note"]

    write_rows(CURVE_FILE, curve_rows, curve_fields)
    write_rows(ROUTE_SUMMARY_FILE, summary_rows, summary_fields)
    write_summary(curve_rows, summary_rows)
    write_report(summary_rows)

    print(f"Wrote {CURVE_FILE}")
    print(f"Wrote {ROUTE_SUMMARY_FILE}")
    print(f"Wrote {SUMMARY_FILE}")
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
