"""Build route-month panel v1 with airport movement supply/context features."""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

PANEL_V0_FILE = PROCESSED_DIR / "route_month_panel_v0.csv"
MOVEMENTS_FILE = PROCESSED_DIR / "statcan_airport_monthly_movements.csv"
PANEL_V1_FILE = PROCESSED_DIR / "route_month_panel_v1.csv"

MOVEMENT_FEATURES = [
    "domestic_total_itinerant_movements",
    "domestic_air_carrier_level_i_iii_movements",
    "domestic_air_carrier_level_iv_vi_movements",
    "domestic_air_carrier_all_levels_movements",
    "transborder_total_itinerant_movements",
    "other_international_total_itinerant_movements",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def movement_lookup() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(MOVEMENTS_FILE)
    return {(row["iata"], row["month"]): row for row in rows}


def add_movement_features(
    output: dict[str, object],
    lookup: dict[tuple[str, str], dict[str, str]],
    *,
    prefix: str,
    iata: str,
    month: str,
) -> None:
    movement_row = lookup.get((iata, month), {})
    for feature in MOVEMENT_FEATURES:
        output[f"{prefix}_{feature}"] = movement_row.get(feature, "")


def build_panel() -> list[dict[str, object]]:
    rows = read_csv(PANEL_V0_FILE)
    movements = movement_lookup()
    output_rows = []

    for row in rows:
        enriched: dict[str, object] = dict(row)
        month = row["month"]
        add_movement_features(
            enriched,
            movements,
            prefix="origin",
            iata=row["origin_iata"],
            month=month,
        )
        add_movement_features(
            enriched,
            movements,
            prefix="destination",
            iata=row["destination_iata"],
            month=month,
        )
        add_movement_features(
            enriched,
            movements,
            prefix="nearest_origin_hub",
            iata=row["nearest_origin_hub_iata"],
            month=month,
        )
        output_rows.append(enriched)

    return output_rows


def non_empty_share(rows: list[dict[str, object]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get(field) not in ("", None)) / len(rows)


def write_summary(rows: list[dict[str, object]]) -> None:
    fields = [
        "origin_domestic_air_carrier_all_levels_movements",
        "destination_domestic_air_carrier_all_levels_movements",
        "nearest_origin_hub_domestic_air_carrier_all_levels_movements",
        "observed_route_passengers",
        "flight_frequency_proxy",
        "route_active",
    ]
    lines = [
        "# Route-Month Panel V1 Summary",
        "",
        f"- Rows: {len(rows):,}",
        f"- Routes: {len({row['route_id'] for row in rows}):,}",
        "",
        "| Field | Non-empty share |",
        "|---|---:|",
    ]
    for field in fields:
        lines.append(f"| {field} | {non_empty_share(rows, field):.1%} |")

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- Airport-month supply/context coverage is now complete for MVP airports.",
            "- Route-level passenger demand and direct OD frequency remain unresolved.",
            "- A credible MVP baseline can model route opportunity using route skeleton features plus airport movement context, while the final model should still seek route-level activity.",
            "",
        ]
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "route_month_panel_v1_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_panel()
    write_csv(PANEL_V1_FILE, rows, list(rows[0].keys()))
    write_summary(rows)
    print(f"Wrote {len(rows):,} rows to {PANEL_V1_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

