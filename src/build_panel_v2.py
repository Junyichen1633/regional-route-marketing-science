"""Build route-month panel v2 with sourced route-active supply features."""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

PANEL_V1_FILE = PROCESSED_DIR / "route_month_panel_v1.csv"
ROUTE_SUPPLY_FILE = PROCESSED_DIR / "route_supply_monthly_v0.csv"
PANEL_V2_FILE = PROCESSED_DIR / "route_month_panel_v2.csv"

SUPPLY_FIELDS = [
    "route_active",
    "weekly_frequency_proxy",
    "route_supply_confidence",
    "route_supply_event_count",
    "route_supply_event_ids",
    "route_supply_carriers",
    "route_supply_evidence_types",
    "route_supply_source_titles",
    "route_supply_source_urls",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def supply_lookup() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(ROUTE_SUPPLY_FILE)
    return {(row["route_id"], row["month"]): row for row in rows}


def build_panel() -> list[dict[str, object]]:
    panel_rows = read_csv(PANEL_V1_FILE)
    supply = supply_lookup()
    output_rows = []

    for row in panel_rows:
        key = (row["route_id"], row["month"])
        supply_row = supply.get(key, {})
        output = dict(row)

        output["route_active"] = supply_row.get("route_active", "")
        output["flight_frequency_proxy"] = supply_row.get("weekly_frequency_proxy", "")
        output["direct_weekly_frequency_proxy"] = supply_row.get("weekly_frequency_proxy", "")
        output["route_supply_confidence"] = supply_row.get("route_supply_confidence", "uncovered")
        output["route_supply_event_count"] = supply_row.get("route_supply_event_count", "0")
        output["route_supply_event_ids"] = supply_row.get("route_supply_event_ids", "")
        output["route_supply_carriers"] = supply_row.get("route_supply_carriers", "")
        output["route_supply_evidence_types"] = supply_row.get("route_supply_evidence_types", "")
        output["route_supply_source_titles"] = supply_row.get("route_supply_source_titles", "")
        output["route_supply_source_urls"] = supply_row.get("route_supply_source_urls", "")

        output_rows.append(output)
    return output_rows


def non_empty_share(rows: list[dict[str, object]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get(field) not in ("", None)) / len(rows)


def write_summary(rows: list[dict[str, object]]) -> None:
    active = sum(1 for row in rows if row.get("route_active") == "1")
    inactive = sum(1 for row in rows if row.get("route_active") == "0")
    uncovered = len(rows) - active - inactive

    lines = [
        "# Route-Month Panel V2 Summary",
        "",
        f"- Rows: {len(rows):,}",
        f"- Routes: {len({row['route_id'] for row in rows}):,}",
        f"- Active route-month labels: {active:,}",
        f"- Inactive route-month labels: {inactive:,}",
        f"- Uncovered route-month labels: {uncovered:,}",
        f"- Route-active coverage: {(active + inactive) / len(rows):.1%}",
        "",
        "| Field | Non-empty share |",
        "|---|---:|",
    ]
    for field in [
        "route_active",
        "direct_weekly_frequency_proxy",
        "route_supply_confidence",
        "origin_domestic_air_carrier_all_levels_movements",
        "destination_domestic_air_carrier_all_levels_movements",
        "nearest_origin_hub_domestic_air_carrier_all_levels_movements",
    ]:
        lines.append(f"| {field} | {non_empty_share(rows, field):.1%} |")

    lines.extend(
        [
            "",
            "Modeling guidance:",
            "",
            "- Use rows with non-empty `route_active` for a first route-active classifier.",
            "- Treat `uncovered` rows as missing labels, not negatives.",
            "- `direct_weekly_frequency_proxy` is an evidence-based proxy, not a complete observed schedule archive.",
            "",
        ]
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "route_month_panel_v2_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_panel()
    write_csv(PANEL_V2_FILE, rows)
    write_summary(rows)
    print(f"Wrote {len(rows):,} rows to {PANEL_V2_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

