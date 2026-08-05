"""Optimize marketing budget allocation across route response curves.

The optimizer is intentionally lightweight and deterministic. It solves a
discrete choice problem: for each route, select one budget level from the
response curve while respecting portfolio constraints.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"

CURVE_FILE = PROCESSED_DIR / "marketing_response_curve_v0.csv"
CASES_FILE = CONFIG_DIR / "budget_optimizer_cases.csv"
ALLOCATIONS_FILE = PROCESSED_DIR / "budget_optimization_allocations_v0.csv"
CASE_SUMMARY_FILE = PROCESSED_DIR / "budget_optimization_case_summary_v0.csv"
SUMMARY_FILE = OUTPUTS_DIR / "budget_optimization_v0_summary.md"
REPORT_FILE = REPORTS_DIR / "phase5_budget_optimization_memo.md"

BUDGET_UNIT_CAD = 25_000


@dataclass(frozen=True)
class Case:
    case_id: str
    scenario: str
    total_budget_cad: int
    objective: str
    allow_relaunch: bool
    max_relaunch_budget_cad: int
    max_budget_per_route_cad: int
    max_routes_funded: int
    min_active_routes_funded: int
    notes: str


@dataclass
class State:
    objective_value: float
    incremental_passenger_proxy: float
    route_health_points: float
    spend_cad: int
    choices: list[dict[str, object]]


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


def load_cases() -> list[Case]:
    cases = []
    for row in read_csv(CASES_FILE):
        cases.append(
            Case(
                case_id=row["case_id"],
                scenario=row["scenario"],
                total_budget_cad=to_int(row["total_budget_cad"]),
                objective=row["objective"],
                allow_relaunch=row["allow_relaunch"] == "1",
                max_relaunch_budget_cad=to_int(row["max_relaunch_budget_cad"]),
                max_budget_per_route_cad=to_int(row["max_budget_per_route_cad"]),
                max_routes_funded=to_int(row["max_routes_funded"]),
                min_active_routes_funded=to_int(row["min_active_routes_funded"]),
                notes=row["notes"],
            )
        )
    return cases


def decision_bucket(row: dict[str, str]) -> str:
    recommendation = row.get("source_recommendation", "")
    if row.get("capacity_required_flag") == "1":
        return "relaunch_feasibility"
    if "Scale or defend" in recommendation:
        return "scale_defend"
    if "Run test" in recommendation:
        return "test_and_learn"
    if "Maintain" in recommendation:
        return "maintain"
    if "Needs schedule data" in recommendation or "Watchlist" in recommendation:
        return "evidence_first"
    return "low_priority"


def portfolio_value(row: dict[str, str]) -> float:
    budget = to_float(row.get("campaign_budget_cad"))
    if budget <= 0:
        return 0.0

    passenger_component = min(to_float(row.get("incremental_passenger_proxy")) / 1_000.0, 6.0)
    health_component = to_float(row.get("incremental_route_health_points"))
    priority_component = to_float(row.get("marketing_support_priority_score_v0")) / 10.0
    value = 0.55 * health_component + 0.30 * passenger_component + 0.15 * priority_component

    bucket = decision_bucket(row)
    bucket_multiplier = {
        "scale_defend": 1.10,
        "test_and_learn": 1.05,
        "relaunch_feasibility": 0.92,
        "maintain": 0.82,
        "evidence_first": 0.72,
        "low_priority": 0.60,
    }.get(bucket, 1.0)
    return value * bucket_multiplier


def objective_value(row: dict[str, str], objective: str) -> float:
    budget = to_float(row.get("campaign_budget_cad"))
    if budget <= 0:
        return 0.0
    if objective == "incremental_passengers":
        return to_float(row.get("incremental_passenger_proxy"))
    if objective == "route_health":
        return to_float(row.get("incremental_route_health_points"))
    if objective == "portfolio_value":
        return portfolio_value(row)
    raise ValueError(f"Unsupported objective: {objective}")


def row_budget_units(row: dict[str, str]) -> int:
    return to_int(row.get("campaign_budget_cad")) // BUDGET_UNIT_CAD


def build_route_options(curve_rows: list[dict[str, str]], case: Case) -> dict[str, list[dict[str, object]]]:
    rows = [
        row
        for row in curve_rows
        if row.get("scenario") == case.scenario
        and to_int(row.get("campaign_budget_cad")) <= case.max_budget_per_route_cad
    ]
    by_route: dict[str, list[dict[str, object]]] = {}

    for row in rows:
        budget = to_int(row.get("campaign_budget_cad"))
        capacity_required = row.get("capacity_required_flag") == "1"
        if capacity_required and budget > 0 and not case.allow_relaunch:
            continue

        option = {
            "route_id": row["route_id"],
            "scenario": row["scenario"],
            "campaign_budget_cad": budget,
            "budget_units": row_budget_units(row),
            "capacity_required_flag": 1 if capacity_required else 0,
            "active_funded_count": 1 if budget > 0 and not capacity_required else 0,
            "funded_count": 1 if budget > 0 else 0,
            "relaunch_budget_units": row_budget_units(row) if budget > 0 and capacity_required else 0,
            "objective_value": objective_value(row, case.objective),
            "incremental_passenger_proxy": to_float(row.get("incremental_passenger_proxy")),
            "incremental_route_health_points": to_float(row.get("incremental_route_health_points")),
            "cost_per_incremental_passenger_proxy_cad": to_float(
                row.get("cost_per_incremental_passenger_proxy_cad")
            ),
            "route_segment": row.get("route_segment", ""),
            "end_of_period_route_status": row.get("end_of_period_route_status", ""),
            "marketing_support_priority_score_v0": to_float(row.get("marketing_support_priority_score_v0")),
            "route_sustainability_score_v0": to_float(row.get("route_sustainability_score_v0")),
            "data_confidence_score": to_float(row.get("data_confidence_score")),
            "source_recommendation": row.get("source_recommendation", ""),
            "decision_bucket": decision_bucket(row),
        }
        by_route.setdefault(row["route_id"], []).append(option)

    for route_id, options in by_route.items():
        zero_options = [option for option in options if option["campaign_budget_cad"] == 0]
        if not zero_options:
            raise ValueError(f"Missing zero-budget option for {route_id}")
        options.sort(key=lambda option: (int(option["campaign_budget_cad"]), -float(option["objective_value"])))

    return by_route


def better_state(candidate: State, incumbent: State | None) -> bool:
    if incumbent is None:
        return True
    candidate_key = (
        candidate.objective_value,
        candidate.route_health_points,
        candidate.incremental_passenger_proxy,
        -candidate.spend_cad,
    )
    incumbent_key = (
        incumbent.objective_value,
        incumbent.route_health_points,
        incumbent.incremental_passenger_proxy,
        -incumbent.spend_cad,
    )
    return candidate_key > incumbent_key


def solve_case(curve_rows: list[dict[str, str]], case: Case) -> tuple[dict[str, object], list[dict[str, object]]]:
    route_options = build_route_options(curve_rows, case)
    route_ids = sorted(route_options)
    total_budget_units = case.total_budget_cad // BUDGET_UNIT_CAD
    max_relaunch_units = case.max_relaunch_budget_cad // BUDGET_UNIT_CAD

    states: dict[tuple[int, int, int, int], State] = {
        (0, 0, 0, 0): State(
            objective_value=0.0,
            incremental_passenger_proxy=0.0,
            route_health_points=0.0,
            spend_cad=0,
            choices=[],
        )
    }

    for route_id in route_ids:
        next_states: dict[tuple[int, int, int, int], State] = {}
        for (spent_units, funded_count, relaunch_units, active_count), state in states.items():
            for option in route_options[route_id]:
                new_spent_units = spent_units + int(option["budget_units"])
                new_funded_count = funded_count + int(option["funded_count"])
                new_relaunch_units = relaunch_units + int(option["relaunch_budget_units"])
                new_active_count = active_count + int(option["active_funded_count"])

                if new_spent_units > total_budget_units:
                    continue
                if new_funded_count > case.max_routes_funded:
                    continue
                if new_relaunch_units > max_relaunch_units:
                    continue

                new_state = State(
                    objective_value=state.objective_value + float(option["objective_value"]),
                    incremental_passenger_proxy=state.incremental_passenger_proxy
                    + float(option["incremental_passenger_proxy"]),
                    route_health_points=state.route_health_points + float(option["incremental_route_health_points"]),
                    spend_cad=state.spend_cad + int(option["campaign_budget_cad"]),
                    choices=state.choices + [option],
                )
                key = (new_spent_units, new_funded_count, new_relaunch_units, new_active_count)
                if better_state(new_state, next_states.get(key)):
                    next_states[key] = new_state
        states = next_states

    feasible = [
        state
        for (spent_units, funded_count, relaunch_units, active_count), state in states.items()
        if active_count >= case.min_active_routes_funded
    ]
    if not feasible:
        raise ValueError(f"No feasible solution for case {case.case_id}")

    best = None
    for state in feasible:
        if better_state(state, best):
            best = state
    assert best is not None

    allocation_rows = [
        {
            "case_id": case.case_id,
            "scenario": case.scenario,
            "objective": case.objective,
            **choice,
        }
        for choice in best.choices
        if int(choice["campaign_budget_cad"]) > 0
    ]
    allocation_rows.sort(key=lambda row: (-int(row["campaign_budget_cad"]), str(row["route_id"])))

    relaunch_budget = sum(
        int(row["campaign_budget_cad"]) for row in allocation_rows if int(row["capacity_required_flag"]) == 1
    )
    case_summary = {
        "case_id": case.case_id,
        "scenario": case.scenario,
        "objective": case.objective,
        "total_budget_cad": case.total_budget_cad,
        "allocated_budget_cad": best.spend_cad,
        "unspent_budget_cad": case.total_budget_cad - best.spend_cad,
        "funded_routes": len(allocation_rows),
        "active_routes_funded": sum(1 for row in allocation_rows if int(row["capacity_required_flag"]) == 0),
        "relaunch_routes_funded": sum(1 for row in allocation_rows if int(row["capacity_required_flag"]) == 1),
        "relaunch_budget_cad": relaunch_budget,
        "incremental_passenger_proxy": best.incremental_passenger_proxy,
        "incremental_route_health_points": best.route_health_points,
        "cost_per_incremental_passenger_proxy_cad": best.spend_cad / best.incremental_passenger_proxy
        if best.incremental_passenger_proxy > 0
        else "",
        "objective_value": best.objective_value,
        "notes": case.notes,
    }
    return case_summary, allocation_rows


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
    if value == "":
        return ""
    return f"${float(value):,.0f}"


def format_number(value: object, digits: int = 0) -> str:
    if value == "":
        return ""
    return f"{float(value):,.{digits}f}"


def format_decimal(value: object, digits: int = 1) -> str:
    if value == "":
        return ""
    return f"{float(value):.{digits}f}"


def case_markdown_table(case_summaries: list[dict[str, object]]) -> list[str]:
    lines = [
        "| Case | Scenario | Objective | Budget | Allocated | Routes | Relaunch budget | Incr. passenger proxy | Health lift pts | Cost / incr. proxy passenger |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in case_summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["case_id"]),
                    str(row["scenario"]),
                    str(row["objective"]),
                    format_money(row["total_budget_cad"]),
                    format_money(row["allocated_budget_cad"]),
                    format_number(row["funded_routes"]),
                    format_money(row["relaunch_budget_cad"]),
                    format_number(row["incremental_passenger_proxy"]),
                    format_decimal(row["incremental_route_health_points"], 1),
                    format_money(row["cost_per_incremental_passenger_proxy_cad"]),
                ]
            )
            + " |"
        )
    return lines


def allocation_markdown_table(rows: list[dict[str, object]], case_id: str) -> list[str]:
    filtered = [row for row in rows if row["case_id"] == case_id]
    lines = [
        "| Route | Budget | Bucket | Incr. passenger proxy | Health lift pts | Recommendation |",
        "|---|---:|---|---:|---:|---|",
    ]
    for row in filtered:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["route_id"]),
                    format_money(row["campaign_budget_cad"]),
                    str(row["decision_bucket"]),
                    format_number(row["incremental_passenger_proxy"]),
                    format_decimal(row["incremental_route_health_points"], 1),
                    str(row["source_recommendation"]),
                ]
            )
            + " |"
        )
    return lines


def write_summary(case_summaries: list[dict[str, object]], allocation_rows: list[dict[str, object]]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    recommended_case = "portfolio_value_500k"
    lines = [
        "# Budget Optimization V0",
        "",
        "This optimizer selects one budget level per route from `marketing_response_curve_v0.csv` under portfolio constraints.",
        "",
        "The solver is a deterministic dynamic program over CAD 25,000 budget increments. No external optimization package is required.",
        "",
        "## Case Summary",
        "",
    ]
    lines.extend(case_markdown_table(case_summaries))
    lines.extend(
        [
            "",
            f"## Recommended Case: `{recommended_case}`",
            "",
        ]
    )
    lines.extend(allocation_markdown_table(allocation_rows, recommended_case))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `portfolio_value_500k` is the recommended planning case because it balances route-health lift, passenger proxy, and strategic priority.",
            "- `growth_passengers_500k` shows what happens when the objective is pure passenger proxy; this is useful but can overweight already-healthy high-volume routes.",
            "- Relaunch candidates are capped separately because marketing cannot create demand without restored airline capacity.",
            "- The optimizer is only as credible as the response assumptions from Phase 4.",
        ]
    )
    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(case_summaries: list[dict[str, object]], allocation_rows: list[dict[str, object]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    recommended_case = "portfolio_value_500k"
    recommended = next(row for row in case_summaries if row["case_id"] == recommended_case)
    lines = [
        "# Phase 5 Memo: Budget Optimization V0",
        "",
        "## Business Question",
        "",
        "Given a fixed regional route marketing budget, which route-budget pairs should be funded under realistic portfolio constraints?",
        "",
        "## Recommended Planning Case",
        "",
        f"The recommended v0 case is `{recommended_case}`.",
        "",
        f"- Total budget: {format_money(recommended['total_budget_cad'])}",
        f"- Allocated budget: {format_money(recommended['allocated_budget_cad'])}",
        f"- Funded routes: {recommended['funded_routes']}",
        f"- Relaunch budget: {format_money(recommended['relaunch_budget_cad'])}",
        f"- Incremental passenger proxy: {format_number(recommended['incremental_passenger_proxy'])}",
        f"- Incremental route-health lift: {format_decimal(recommended['incremental_route_health_points'], 1)} points",
        f"- Cost per incremental proxy passenger: {format_money(recommended['cost_per_incremental_passenger_proxy_cad'])}",
        "",
        "## Recommended Allocation",
        "",
    ]
    lines.extend(allocation_markdown_table(allocation_rows, recommended_case))
    lines.extend(
        [
            "",
            "## Why This Is Useful",
            "",
            "The optimizer makes the tradeoff explicit: a passenger-maximizing objective, a health-lift objective, and a balanced portfolio objective can recommend different allocations. This is the kind of business-facing modeling decision a product data scientist should be able to explain.",
            "",
            "## Guardrails",
            "",
            "- Treat all passenger results as proxy outcomes, not observed passengers.",
            "- Keep relaunch allocations in a separate bucket until airline capacity is confirmed.",
            "- Do not use this as a media plan without validating route-level spend and passenger outcomes.",
            "",
            "## Next Step",
            "",
            "Design an experiment plan for the recommended active-route tests and relaunch feasibility candidates.",
        ]
    )
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    curve_rows = read_csv(CURVE_FILE)
    cases = load_cases()

    case_summaries = []
    allocation_rows = []
    for case in cases:
        case_summary, case_allocations = solve_case(curve_rows, case)
        case_summaries.append(case_summary)
        allocation_rows.extend(case_allocations)

    case_fields = [
        "case_id",
        "scenario",
        "objective",
        "total_budget_cad",
        "allocated_budget_cad",
        "unspent_budget_cad",
        "funded_routes",
        "active_routes_funded",
        "relaunch_routes_funded",
        "relaunch_budget_cad",
        "incremental_passenger_proxy",
        "incremental_route_health_points",
        "cost_per_incremental_passenger_proxy_cad",
        "objective_value",
        "notes",
    ]
    allocation_fields = [
        "case_id",
        "scenario",
        "objective",
        "route_id",
        "campaign_budget_cad",
        "route_segment",
        "end_of_period_route_status",
        "capacity_required_flag",
        "decision_bucket",
        "incremental_passenger_proxy",
        "incremental_route_health_points",
        "cost_per_incremental_passenger_proxy_cad",
        "marketing_support_priority_score_v0",
        "route_sustainability_score_v0",
        "data_confidence_score",
        "source_recommendation",
    ]

    write_rows(CASE_SUMMARY_FILE, case_summaries, case_fields)
    write_rows(ALLOCATIONS_FILE, allocation_rows, allocation_fields)
    write_summary(case_summaries, allocation_rows)
    write_report(case_summaries, allocation_rows)

    print(f"Wrote {CASE_SUMMARY_FILE}")
    print(f"Wrote {ALLOCATIONS_FILE}")
    print(f"Wrote {SUMMARY_FILE}")
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
