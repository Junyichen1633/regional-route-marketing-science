"""Build the first enriched route-month panel."""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

SKELETON_FILE = PROCESSED_DIR / "route_month_skeleton.csv"
MONTHLY_SCREENED_FILE = PROCESSED_DIR / "statcan_screened_monthly_passengers.csv"
ANNUAL_AIRPORT_FILE = PROCESSED_DIR / "statcan_airport_annual_passengers.csv"
PANEL_V0_FILE = PROCESSED_DIR / "route_month_panel_v0.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def screened_lookup() -> dict[tuple[str, str], int]:
    rows = read_csv(MONTHLY_SCREENED_FILE)
    return {
        (row["iata"], row["month"]): int(row["value"])
        for row in rows
        if row["value"]
    }


def annual_lookup() -> dict[tuple[str, str], int]:
    rows = read_csv(ANNUAL_AIRPORT_FILE)
    return {
        (row["iata"], row["year"]): int(row["value"])
        for row in rows
        if row["value"]
    }


def build_panel() -> list[dict[str, object]]:
    skeleton_rows = read_csv(SKELETON_FILE)
    monthly = screened_lookup()
    annual = annual_lookup()

    panel_rows: list[dict[str, object]] = []
    for row in skeleton_rows:
        month = row["month"]
        year = row["year"]
        origin = row["origin_iata"]
        destination = row["destination_iata"]
        nearest_hub = row["nearest_origin_hub_iata"]

        enriched = dict(row)
        enriched["origin_monthly_screened_passengers"] = monthly.get((origin, month), "")
        enriched["destination_monthly_screened_passengers"] = monthly.get((destination, month), "")
        enriched["nearest_origin_hub_monthly_screened_passengers"] = monthly.get(
            (nearest_hub, month),
            "",
        )
        enriched["origin_annual_passengers"] = annual.get((origin, year), "")
        enriched["destination_annual_passengers"] = annual.get((destination, year), "")
        enriched["nearest_origin_hub_annual_passengers"] = annual.get((nearest_hub, year), "")
        enriched["observed_route_passengers"] = ""
        enriched["flight_frequency_proxy"] = ""
        enriched["route_active"] = ""
        enriched["simulated_marketing_spend"] = ""
        panel_rows.append(enriched)

    return panel_rows


def non_empty_share(rows: list[dict[str, object]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get(field) not in ("", None)) / len(rows)


def write_summary(rows: list[dict[str, object]]) -> None:
    fields = [
        "origin_monthly_screened_passengers",
        "destination_monthly_screened_passengers",
        "nearest_origin_hub_monthly_screened_passengers",
        "origin_annual_passengers",
        "destination_annual_passengers",
        "nearest_origin_hub_annual_passengers",
        "observed_route_passengers",
        "flight_frequency_proxy",
        "route_active",
    ]
    lines = [
        "# Route-Month Panel V0 Summary",
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
            "- Hub context is available for routes whose origin, destination, or nearest competing hub is one of the covered major airports.",
            "- Regional route outcomes are still missing; the next data task is route activity and flight frequency.",
            "- The blank marketing field is intentional and should remain blank until scenario assumptions are documented.",
            "",
        ]
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "route_month_panel_v0_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_panel()
    write_csv(PANEL_V0_FILE, rows, list(rows[0].keys()))
    write_summary(rows)
    print(f"Wrote {len(rows):,} rows to {PANEL_V0_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

