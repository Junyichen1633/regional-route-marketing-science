"""Build processed context tables from downloaded Statistics Canada data."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
RAW_STATCAN_DIR = PROJECT_ROOT / "data" / "raw" / "statcan"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

ANNUAL_TRAFFIC_FILE = RAW_STATCAN_DIR / "23100253" / "23100253.csv"
MONTHLY_SCREENED_FILE = RAW_STATCAN_DIR / "23100312" / "23100312.csv"

START_YEAR = 2020
END_YEAR = 2025


def load_geo_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    with (CONFIG_DIR / "statcan_airport_geo_aliases.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["statcan_geo"]:
                aliases[row["statcan_geo"]] = row["iata"]
    return aliases


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_annual_airport_context(geo_aliases: dict[str, str]) -> list[dict[str, object]]:
    rows = []
    for row in read_csv(ANNUAL_TRAFFIC_FILE):
        if row["GEO"] not in geo_aliases:
            continue
        if row["Air passenger traffic"] != "Total, passengers enplaned and deplaned":
            continue
        year = int(row["REF_DATE"])
        if not START_YEAR <= year <= END_YEAR:
            continue
        rows.append(
            {
                "iata": geo_aliases[row["GEO"]],
                "year": year,
                "statcan_geo": row["GEO"],
                "metric": "total_passengers_enplaned_deplaned",
                "value": int(float(row["VALUE"])) if row["VALUE"] else "",
                "source_table": "23100253",
            }
        )
    return sorted(rows, key=lambda item: (item["iata"], item["year"]))


def build_monthly_screened_context(geo_aliases: dict[str, str]) -> list[dict[str, object]]:
    rows = []
    for row in read_csv(MONTHLY_SCREENED_FILE):
        if row["GEO"] not in geo_aliases:
            continue
        if row["Screened traffic"] != "Total passengers":
            continue
        year = int(row["REF_DATE"][:4])
        if not START_YEAR <= year <= END_YEAR:
            continue
        rows.append(
            {
                "iata": geo_aliases[row["GEO"]],
                "month": f"{row['REF_DATE']}-01",
                "statcan_geo": row["GEO"],
                "metric": "total_screened_passengers",
                "value": int(float(row["VALUE"])) if row["VALUE"] else "",
                "source_table": "23100312",
            }
        )
    return sorted(rows, key=lambda item: (item["iata"], item["month"]))


def write_coverage_report(
    annual_rows: list[dict[str, object]],
    monthly_rows: list[dict[str, object]],
) -> None:
    annual_years: dict[str, set[int]] = defaultdict(set)
    monthly_months: dict[str, set[str]] = defaultdict(set)
    for row in annual_rows:
        annual_years[str(row["iata"])].add(int(row["year"]))
    for row in monthly_rows:
        monthly_months[str(row["iata"])].add(str(row["month"]))

    iatas = sorted(set(annual_years) | set(monthly_months))
    lines = [
        "# Processed StatsCan Context Tables",
        "",
        "| IATA | Annual airport traffic years | Monthly screened months |",
        "|---|---:|---:|",
    ]
    for iata in iatas:
        years = sorted(annual_years.get(iata, set()))
        months = sorted(monthly_months.get(iata, set()))
        years_text = f"{years[0]}-{years[-1]}" if years else "none"
        lines.append(f"| {iata} | {years_text} | {len(months)} |")

    lines.extend(
        [
            "",
            "Notes:",
            "",
            "- Annual airport traffic is airport-level and useful for broad calibration.",
            "- Monthly screened traffic is hub-context data for major airports only.",
            "- Neither table provides route-month passenger counts.",
            "",
        ]
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "statcan_context_tables_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    geo_aliases = load_geo_aliases()
    annual_rows = build_annual_airport_context(geo_aliases)
    monthly_rows = build_monthly_screened_context(geo_aliases)

    write_csv(
        PROCESSED_DIR / "statcan_airport_annual_passengers.csv",
        annual_rows,
        ["iata", "year", "statcan_geo", "metric", "value", "source_table"],
    )
    write_csv(
        PROCESSED_DIR / "statcan_screened_monthly_passengers.csv",
        monthly_rows,
        ["iata", "month", "statcan_geo", "metric", "value", "source_table"],
    )
    write_coverage_report(annual_rows, monthly_rows)
    print(f"Wrote {len(annual_rows):,} annual rows.")
    print(f"Wrote {len(monthly_rows):,} monthly screened rows.")


if __name__ == "__main__":
    main()

