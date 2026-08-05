"""Expand sourced route supply events into monthly route-active features."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

EVENTS_FILE = CONFIG_DIR / "route_supply_events.csv"
SKELETON_FILE = PROCESSED_DIR / "route_month_skeleton.csv"
MONTHLY_SUPPLY_FILE = PROCESSED_DIR / "route_supply_monthly_v0.csv"

CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass(frozen=True)
class SupplyEvent:
    route_id: str
    event_id: str
    start_month: date
    end_month: date
    route_active: int
    weekly_frequency_proxy: float | None
    carrier: str
    evidence_type: str
    confidence: str
    source_title: str
    source_url: str
    evidence_note: str


def parse_month(value: str) -> date:
    return date.fromisoformat(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_events() -> list[SupplyEvent]:
    events: list[SupplyEvent] = []
    for row in read_csv(EVENTS_FILE):
        frequency = row["weekly_frequency_proxy"]
        events.append(
            SupplyEvent(
                route_id=row["route_id"],
                event_id=row["event_id"],
                start_month=parse_month(row["start_month"]),
                end_month=parse_month(row["end_month"]),
                route_active=int(row["route_active"]),
                weekly_frequency_proxy=float(frequency) if frequency else None,
                carrier=row["carrier"],
                evidence_type=row["evidence_type"],
                confidence=row["confidence"],
                source_title=row["source_title"],
                source_url=row["source_url"],
                evidence_note=row["evidence_note"],
            )
        )
    return events


def events_for_month(events: list[SupplyEvent], route_id: str, month: date) -> list[SupplyEvent]:
    return [
        event
        for event in events
        if event.route_id == route_id and event.start_month <= month <= event.end_month
    ]


def choose_confidence(events: list[SupplyEvent]) -> str:
    if not events:
        return "uncovered"
    return max(events, key=lambda event: CONFIDENCE_RANK.get(event.confidence, 0)).confidence


def choose_frequency(events: list[SupplyEvent]) -> float | str:
    values = [
        event.weekly_frequency_proxy
        for event in events
        if event.route_active == 1 and event.weekly_frequency_proxy is not None
    ]
    if not values:
        return ""
    return max(values)


def unique_join(values: list[str]) -> str:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return "|".join(seen)


def summarize_event_set(events: list[SupplyEvent]) -> dict[str, object]:
    if not events:
        return {
            "route_active": "",
            "weekly_frequency_proxy": "",
            "route_supply_confidence": "uncovered",
            "route_supply_event_count": 0,
            "route_supply_event_ids": "",
            "route_supply_carriers": "",
            "route_supply_evidence_types": "",
            "route_supply_source_titles": "",
            "route_supply_source_urls": "",
        }

    active_events = [event for event in events if event.route_active == 1]
    inactive_events = [event for event in events if event.route_active == 0]
    if active_events:
        route_active: int | str = 1
    elif inactive_events:
        route_active = 0
    else:
        route_active = ""

    return {
        "route_active": route_active,
        "weekly_frequency_proxy": choose_frequency(events),
        "route_supply_confidence": choose_confidence(events),
        "route_supply_event_count": len(events),
        "route_supply_event_ids": unique_join([event.event_id for event in events]),
        "route_supply_carriers": unique_join([event.carrier for event in events]),
        "route_supply_evidence_types": unique_join([event.evidence_type for event in events]),
        "route_supply_source_titles": unique_join([event.source_title for event in events]),
        "route_supply_source_urls": unique_join([event.source_url for event in events]),
    }


def build_monthly_supply() -> list[dict[str, object]]:
    events = read_events()
    skeleton_rows = read_csv(SKELETON_FILE)
    output_rows = []
    for row in skeleton_rows:
        month = parse_month(row["month"])
        matching_events = events_for_month(events, row["route_id"], month)
        supply_fields = summarize_event_set(matching_events)
        output = {
            "route_id": row["route_id"],
            "origin_iata": row["origin_iata"],
            "destination_iata": row["destination_iata"],
            "month": row["month"],
            **supply_fields,
        }
        output_rows.append(output)
    return output_rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, object]]) -> None:
    route_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    active_count = 0
    inactive_count = 0
    uncovered_count = 0

    for row in rows:
        route_id = str(row["route_id"])
        status = row["route_active"]
        if status == 1:
            active_count += 1
            route_counts[route_id]["active"] += 1
        elif status == 0:
            inactive_count += 1
            route_counts[route_id]["inactive"] += 1
        else:
            uncovered_count += 1
            route_counts[route_id]["uncovered"] += 1

    lines = [
        "# Route Supply Monthly V0 Summary",
        "",
        f"- Rows: {len(rows):,}",
        f"- Active route-months: {active_count:,}",
        f"- Inactive route-months: {inactive_count:,}",
        f"- Uncovered route-months: {uncovered_count:,}",
        f"- Coverage: {(active_count + inactive_count) / len(rows):.1%}",
        "",
        "| Route | Active months | Inactive months | Uncovered months |",
        "|---|---:|---:|---:|",
    ]

    for route_id in sorted(route_counts):
        counts = route_counts[route_id]
        lines.append(
            f"| {route_id} | {counts['active']} | {counts['inactive']} | {counts['uncovered']} |"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- This is a sourced route-active layer, not a complete authoritative schedule archive.",
            "- Blank route-active months should be treated as uncovered rather than inactive.",
            "- For modeling, use rows with covered active/inactive labels first, or add a documented imputation layer later.",
            "",
        ]
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "route_supply_monthly_v0_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_monthly_supply()
    write_csv(MONTHLY_SUPPLY_FILE, rows)
    write_summary(rows)
    print(f"Wrote {len(rows):,} route-month supply rows.")


if __name__ == "__main__":
    main()

