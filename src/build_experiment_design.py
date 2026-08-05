"""Build experiment recommendations for the optimized route portfolio.

This phase turns model recommendations into validation plans. It does not run a
statistical test; it specifies the treatment/control design, metrics, guardrails,
and decision rules needed to validate the recommended allocation.
"""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"

ALLOCATIONS_FILE = PROCESSED_DIR / "budget_optimization_allocations_v0.csv"
SCORES_FILE = PROCESSED_DIR / "route_opportunity_score_v0.csv"
CURVE_FILE = PROCESSED_DIR / "marketing_response_curve_v0.csv"
ASSUMPTIONS_FILE = CONFIG_DIR / "experiment_design_assumptions.csv"

EXPERIMENT_PLAN_FILE = PROCESSED_DIR / "experiment_design_plan_v0.csv"
CONTROL_MATCHES_FILE = PROCESSED_DIR / "experiment_control_matches_v0.csv"
SUMMARY_FILE = OUTPUTS_DIR / "experiment_design_v0_summary.md"
REPORT_FILE = REPORTS_DIR / "phase6_experiment_design_memo.md"

RECOMMENDED_CASE_ID = "portfolio_value_500k"
CONTROL_MATCH_COUNT = 3


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


def score_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["route_id"]: row for row in rows}


def assumption_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["decision_bucket"]: row for row in rows}


def curve_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], dict[str, str]]:
    return {
        (row["route_id"], row["scenario"], to_int(row["campaign_budget_cad"])): row
        for row in rows
    }


def normalized_frequency(row: dict[str, str]) -> float:
    frequency = to_float(row.get("median_weekly_frequency_proxy_2023_2025"))
    return min(frequency, 14.0) / 14.0 if frequency > 0 else 0.0


def match_distance(treatment: dict[str, str], candidate: dict[str, str]) -> float:
    score = 0.0
    if candidate.get("model_role") != "target":
        score += 35.0 if candidate.get("model_role") == "benchmark" else 25.0
    if treatment.get("route_segment") != candidate.get("route_segment"):
        score += 20.0
    if treatment.get("end_of_period_route_status") != candidate.get("end_of_period_route_status"):
        score += 18.0
    if treatment.get("destination_iata") != candidate.get("destination_iata"):
        score += 8.0
    if treatment.get("origin_iata") == candidate.get("origin_iata"):
        score += 4.0

    numeric_weights = [
        ("distance_km", 3_500.0, 14.0),
        ("demand_context_score", 100.0, 18.0),
        ("route_sustainability_score_v0", 100.0, 14.0),
        ("marketing_support_priority_score_v0", 100.0, 12.0),
        ("competition_pressure_score", 100.0, 8.0),
        ("data_confidence_score", 100.0, 6.0),
    ]
    for field, scale, weight in numeric_weights:
        score += min(abs(to_float(treatment.get(field)) - to_float(candidate.get(field))) / scale, 1.0) * weight

    score += abs(normalized_frequency(treatment) - normalized_frequency(candidate)) * 8.0
    return score


def match_notes(treatment: dict[str, str], candidate: dict[str, str]) -> str:
    notes = []
    if treatment.get("route_segment") == candidate.get("route_segment"):
        notes.append("same segment")
    else:
        notes.append("different segment")
    if treatment.get("destination_iata") == candidate.get("destination_iata"):
        notes.append("same destination")
    if treatment.get("origin_iata") == candidate.get("origin_iata"):
        notes.append("same origin; monitor spillover")
    if candidate.get("model_role") != "target":
        notes.append(f"{candidate.get('model_role')} role")
    return "; ".join(notes)


def select_controls(
    treatment_route_id: str,
    scores: dict[str, dict[str, str]],
    funded_route_ids: set[str],
) -> list[dict[str, object]]:
    treatment = scores[treatment_route_id]
    primary_candidates = [
        row
        for route_id, row in scores.items()
        if route_id not in funded_route_ids
        and route_id != treatment_route_id
        and row.get("model_role") == "target"
    ]
    fallback_candidates = [
        row
        for route_id, row in scores.items()
        if route_id not in funded_route_ids
        and route_id != treatment_route_id
        and row not in primary_candidates
    ]
    candidates = primary_candidates + fallback_candidates
    ranked = sorted(candidates, key=lambda row: (match_distance(treatment, row), row["route_id"]))
    matches = []
    for rank, candidate in enumerate(ranked[:CONTROL_MATCH_COUNT], start=1):
        matches.append(
            {
                "treatment_route_id": treatment_route_id,
                "control_route_id": candidate["route_id"],
                "match_rank": rank,
                "match_score": match_distance(treatment, candidate),
                "control_model_role": candidate.get("model_role", ""),
                "control_route_segment": candidate.get("route_segment", ""),
                "control_end_status": candidate.get("end_of_period_route_status", ""),
                "control_recommendation": candidate.get("recommendation", ""),
                "match_notes": match_notes(treatment, candidate),
            }
        )
    return matches


def power_readiness(row: dict[str, str], curve_row: dict[str, str]) -> str:
    if row.get("capacity_required_flag") == "1":
        return "Feasibility only until capacity is committed"

    incremental = to_float(row.get("incremental_passenger_proxy"))
    baseline = to_float(curve_row.get("baseline_annual_passenger_proxy"))
    data_confidence = to_float(row.get("data_confidence_score"))
    if incremental >= 2_000 and baseline >= 75_000 and data_confidence >= 70:
        return "Medium; validate with booking or search-conversion data"
    if incremental >= 1_000 and data_confidence >= 50:
        return "Directional; pool with similar routes or extend test window"
    return "Low; use guardrail KPIs rather than definitive lift claim"


def planned_mde_pct(row: dict[str, str], curve_row: dict[str, str]) -> float:
    expected_pct = to_float(curve_row.get("incremental_pct_of_baseline_proxy"))
    bucket = row.get("decision_bucket", "")
    floor = 0.035 if bucket in {"scale_defend", "test_and_learn"} else 0.025
    if bucket == "relaunch_feasibility":
        floor = 0.080
    return max(floor, min(0.15, expected_pct * 1.5))


def decision_rules(row: dict[str, str], assumption: dict[str, str]) -> tuple[str, str, str]:
    expected_incremental = to_float(row.get("incremental_passenger_proxy"))
    scale_ratio = to_float(assumption.get("scale_success_ratio"), default=1.0)
    maintain_ratio = to_float(assumption.get("maintain_success_ratio"), default=0.5)
    bucket = row.get("decision_bucket", "")

    if bucket == "relaunch_feasibility":
        scale = (
            "Advance to airline/capacity negotiation if qualified demand signal reaches "
            f"{scale_ratio:.0%} of base target and capacity partner interest is confirmed"
        )
        maintain = (
            "Continue validation if qualified demand signal reaches "
            f"{maintain_ratio:.0%}-{scale_ratio:.0%} of base target"
        )
        stop = "Stop relaunch spend if demand signal is below maintain threshold or capacity is unavailable"
        return scale, maintain, stop

    scale = f"Scale if observed incremental lift is >= {scale_ratio:.0%} of base target ({expected_incremental * scale_ratio:,.0f} proxy passengers)"
    maintain = f"Maintain or retest if observed lift is {maintain_ratio:.0%}-{scale_ratio:.0%} of base target"
    stop = f"Stop or redesign if observed lift is < {maintain_ratio:.0%} of base target or guardrails fail"
    return scale, maintain, stop


def build_plan_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    allocations = [
        row for row in read_csv(ALLOCATIONS_FILE) if row["case_id"] == RECOMMENDED_CASE_ID
    ]
    scores = score_lookup(read_csv(SCORES_FILE))
    curves = curve_lookup(read_csv(CURVE_FILE))
    assumptions = assumption_lookup(read_csv(ASSUMPTIONS_FILE))
    funded_route_ids = {row["route_id"] for row in allocations}

    plan_rows: list[dict[str, object]] = []
    match_rows: list[dict[str, object]] = []

    for allocation in allocations:
        route_id = allocation["route_id"]
        score_row = scores[route_id]
        budget = to_int(allocation["campaign_budget_cad"])
        scenario = allocation["scenario"]
        curve_row = curves[(route_id, scenario, budget)]
        assumption = assumptions[allocation["decision_bucket"]]
        controls = select_controls(route_id, scores, funded_route_ids)
        match_rows.extend(controls)

        scale_rule, maintain_rule, stop_rule = decision_rules(allocation, assumption)
        control_ids = [str(control["control_route_id"]) for control in controls]
        while len(control_ids) < CONTROL_MATCH_COUNT:
            control_ids.append("")

        plan_rows.append(
            {
                "case_id": RECOMMENDED_CASE_ID,
                "route_id": route_id,
                "campaign_budget_cad": budget,
                "decision_bucket": allocation["decision_bucket"],
                "experiment_design": assumption["experiment_design"],
                "route_segment": allocation["route_segment"],
                "end_of_period_route_status": allocation["end_of_period_route_status"],
                "capacity_required_flag": allocation["capacity_required_flag"],
                "primary_metric": assumption["primary_metric"],
                "secondary_metrics": assumption["secondary_metrics"],
                "comparison_route_1": control_ids[0],
                "comparison_route_2": control_ids[1],
                "comparison_route_3": control_ids[2],
                "pre_period_weeks": assumption["pre_period_weeks"],
                "test_period_weeks": assumption["test_period_weeks"],
                "post_period_weeks": assumption["post_period_weeks"],
                "baseline_annual_passenger_proxy": to_float(curve_row.get("baseline_annual_passenger_proxy")),
                "expected_incremental_passenger_proxy": to_float(allocation.get("incremental_passenger_proxy")),
                "expected_incremental_pct_of_baseline_proxy": to_float(curve_row.get("incremental_pct_of_baseline_proxy")),
                "planned_mde_pct": planned_mde_pct(allocation, curve_row),
                "power_readiness": power_readiness(allocation, curve_row),
                "scale_decision_rule": scale_rule,
                "maintain_decision_rule": maintain_rule,
                "stop_decision_rule": stop_rule,
                "guardrail": assumption["guardrail"],
                "data_confidence_score": allocation["data_confidence_score"],
                "route_sustainability_score_v0": allocation["route_sustainability_score_v0"],
                "marketing_support_priority_score_v0": allocation["marketing_support_priority_score_v0"],
                "source_recommendation": allocation["source_recommendation"],
            }
        )

    plan_rows.sort(key=lambda row: (-int(row["campaign_budget_cad"]), str(row["route_id"])))
    match_rows.sort(key=lambda row: (str(row["treatment_route_id"]), int(row["match_rank"])))
    return plan_rows, match_rows


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
                    formatted[field] = f"{value:.4f}"
                else:
                    formatted[field] = value
            writer.writerow(formatted)


def format_money(value: object) -> str:
    return f"${float(value):,.0f}"


def format_number(value: object, digits: int = 0) -> str:
    return f"{float(value):,.{digits}f}"


def format_percent(value: object) -> str:
    return f"{float(value):.1%}"


def plan_table(rows: list[dict[str, object]]) -> list[str]:
    lines = [
        "| Route | Budget | Design | Primary metric | Controls | Expected lift | MDE | Power readiness |",
        "|---|---:|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        controls = ", ".join(
            control
            for control in [
                str(row["comparison_route_1"]),
                str(row["comparison_route_2"]),
                str(row["comparison_route_3"]),
            ]
            if control
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["route_id"]),
                    format_money(row["campaign_budget_cad"]),
                    str(row["experiment_design"]),
                    str(row["primary_metric"]),
                    controls,
                    format_number(row["expected_incremental_passenger_proxy"]),
                    format_percent(row["planned_mde_pct"]),
                    str(row["power_readiness"]),
                ]
            )
            + " |"
        )
    return lines


def write_summary(plan_rows: list[dict[str, object]], match_rows: list[dict[str, object]]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    active_tests = [row for row in plan_rows if row["capacity_required_flag"] == "0"]
    relaunch_tests = [row for row in plan_rows if row["capacity_required_flag"] == "1"]
    total_budget = sum(int(row["campaign_budget_cad"]) for row in plan_rows)

    lines = [
        "# Experiment Design V0",
        "",
        f"This plan validates the `{RECOMMENDED_CASE_ID}` budget allocation.",
        "",
        "## Scope",
        "",
        f"- Funded routes: {len(plan_rows)}",
        f"- Active-route tests: {len(active_tests)}",
        f"- Relaunch feasibility tests: {len(relaunch_tests)}",
        f"- Total test budget: {format_money(total_budget)}",
        f"- Control matches generated: {len(match_rows)}",
        "",
        "## Route-Level Test Plan",
        "",
    ]
    lines.extend(plan_table(plan_rows))
    lines.extend(
        [
            "",
            "## Measurement Positioning",
            "",
            "- Active-route tests can be evaluated as matched-route or geo-lift experiments if booking/search-conversion data is available.",
            "- Relaunch routes are capacity-gated feasibility tests; demand signals should not be called passenger lift until service is restorable.",
            "- Public airport data alone is not enough for final incrementality measurement.",
            "- The experiment plan is designed to specify the partner data required to validate the model.",
        ]
    )
    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(plan_rows: list[dict[str, object]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    relaunch = [row for row in plan_rows if row["capacity_required_flag"] == "1"]
    active = [row for row in plan_rows if row["capacity_required_flag"] == "0"]

    lines = [
        "# Phase 6 Memo: Experiment Design V0",
        "",
        "## Business Question",
        "",
        "How should the recommended marketing allocation be validated before scaling spend or using the model operationally?",
        "",
        "## Recommendation",
        "",
        "Run a staged validation program rather than treating the optimizer as final truth.",
        "",
        f"- Active-route tests: {len(active)}",
        f"- Relaunch feasibility tests: {len(relaunch)}",
        f"- Recommended total test budget: {format_money(sum(int(row['campaign_budget_cad']) for row in plan_rows))}",
        "",
        "## Test Plan",
        "",
    ]
    lines.extend(plan_table(plan_rows))
    lines.extend(
        [
            "",
            "## Decision Rules",
            "",
            "For active routes, scale only when observed incremental lift reaches the route-specific success threshold and guardrails hold. For relaunch routes, advance only if qualified demand signals and airline capacity both clear the gate.",
            "",
            "## Data Required",
            "",
            "- Route-level bookings or booking proxy by origin catchment and week",
            "- Campaign spend and impressions by route and market",
            "- Route page/search conversion events",
            "- Load factor or capacity proxy",
            "- Fare/yield guardrail if available",
            "",
            "## Next Step",
            "",
            "Package the project into an executive portfolio artifact with the business narrative, data caveats, model flow, recommendations, and validation plan.",
        ]
    )
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    plan_rows, match_rows = build_plan_rows()
    plan_fields = [
        "case_id",
        "route_id",
        "campaign_budget_cad",
        "decision_bucket",
        "experiment_design",
        "route_segment",
        "end_of_period_route_status",
        "capacity_required_flag",
        "primary_metric",
        "secondary_metrics",
        "comparison_route_1",
        "comparison_route_2",
        "comparison_route_3",
        "pre_period_weeks",
        "test_period_weeks",
        "post_period_weeks",
        "baseline_annual_passenger_proxy",
        "expected_incremental_passenger_proxy",
        "expected_incremental_pct_of_baseline_proxy",
        "planned_mde_pct",
        "power_readiness",
        "scale_decision_rule",
        "maintain_decision_rule",
        "stop_decision_rule",
        "guardrail",
        "data_confidence_score",
        "route_sustainability_score_v0",
        "marketing_support_priority_score_v0",
        "source_recommendation",
    ]
    match_fields = [
        "treatment_route_id",
        "control_route_id",
        "match_rank",
        "match_score",
        "control_model_role",
        "control_route_segment",
        "control_end_status",
        "control_recommendation",
        "match_notes",
    ]

    write_rows(EXPERIMENT_PLAN_FILE, plan_rows, plan_fields)
    write_rows(CONTROL_MATCHES_FILE, match_rows, match_fields)
    write_summary(plan_rows, match_rows)
    write_report(plan_rows)

    print(f"Wrote {EXPERIMENT_PLAN_FILE}")
    print(f"Wrote {CONTROL_MATCHES_FILE}")
    print(f"Wrote {SUMMARY_FILE}")
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
