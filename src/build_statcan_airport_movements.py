"""Build monthly airport movement context from StatsCan 23-10-0302-01."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
RAW_STATCAN_DIR = PROJECT_ROOT / "data" / "raw" / "statcan" / "23100302"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

MOVEMENTS_FILE = RAW_STATCAN_DIR / "23100302.csv"
START_YEAR = 2020
END_YEAR = 2025

MOVEMENT_FIELD = "Domestic and international itinerant movements"
TYPE_FIELD = "Type of operation"

FEATURE_MAP = {
    ("Domestic movements", "Total itinerant movements"): "domestic_total_itinerant_movements",
    (
        "Domestic movements",
        "Air carrier movements, level I-III including foreign air carriers",
    ): "domestic_air_carrier_level_i_iii_movements",
    ("Domestic movements", "Air carrier movements, level IV-VI"): "domestic_air_carrier_level_iv_vi_movements",
    ("Transborder movements", "Total itinerant movements"): "transborder_total_itinerant_movements",
    ("Other international movements", "Total itinerant movements"): "other_international_total_itinerant_movements",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_aliases() -> dict[str, str]:
    aliases = {}
    with (CONFIG_DIR / "statcan_airport_movements_aliases.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        for row in csv.DictReader(handle):
            aliases[row["statcan_airport"]] = row["iata"]
    return aliases


def parse_value(value: str) -> int | str:
    if value == "":
        return ""
    return int(float(value))


def build_movements_table() -> list[dict[str, object]]:
    aliases = load_aliases()
    grouped: dict[tuple[str, str], dict[str, object]] = defaultdict(dict)

    for row in read_csv(MOVEMENTS_FILE):
        airport_name = row["Airports"]
        if airport_name not in aliases:
            continue
        year = int(row["REF_DATE"][:4])
        if not START_YEAR <= year <= END_YEAR:
            continue
        feature = FEATURE_MAP.get((row[MOVEMENT_FIELD], row[TYPE_FIELD]))
        if feature is None:
            continue

        key = (aliases[airport_name], f"{row['REF_DATE']}-01")
        grouped[key]["iata"] = aliases[airport_name]
        grouped[key]["month"] = f"{row['REF_DATE']}-01"
        grouped[key]["statcan_airport"] = airport_name
        grouped[key][feature] = parse_value(row["VALUE"])

    output_rows = []
    features = list(FEATURE_MAP.values())
    for key in sorted(grouped):
        row = grouped[key]
        for feature in features:
            row.setdefault(feature, "")

        domestic_i_iii = row["domestic_air_carrier_level_i_iii_movements"] or 0
        domestic_iv_vi = row["domestic_air_carrier_level_iv_vi_movements"] or 0
        if domestic_i_iii == "" and domestic_iv_vi == "":
            row["domestic_air_carrier_all_levels_movements"] = ""
        else:
            row["domestic_air_carrier_all_levels_movements"] = int(domestic_i_iii) + int(domestic_iv_vi)

        row["source_table"] = "23100302"
        output_rows.append(row)
    return output_rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "iata",
        "month",
        "statcan_airport",
        "domestic_total_itinerant_movements",
        "domestic_air_carrier_level_i_iii_movements",
        "domestic_air_carrier_level_iv_vi_movements",
        "domestic_air_carrier_all_levels_movements",
        "transborder_total_itinerant_movements",
        "other_international_total_itinerant_movements",
        "source_table",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, object]]) -> None:
    by_airport: dict[str, int] = defaultdict(int)
    for row in rows:
        by_airport[str(row["iata"])] += 1

    lines = [
        "# StatsCan Airport Movements Summary",
        "",
        "Source: Statistics Canada Table 23-10-0302-01.",
        "",
        "| IATA | Monthly rows |",
        "|---|---:|",
    ]
    for iata, count in sorted(by_airport.items()):
        lines.append(f"| {iata} | {count} |")

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- This table provides airport-month supply/activity context for every MVP airport.",
            "- It does not identify destination airport, so it is not a route-level frequency table.",
            "- The strongest baseline use is as origin/destination airport activity context and a supply-pressure proxy.",
            "",
        ]
    )
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "statcan_airport_movements_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_movements_table()
    write_csv(PROCESSED_DIR / "statcan_airport_monthly_movements.csv", rows)
    write_summary(rows)
    print(f"Wrote {len(rows):,} airport-month movement rows.")


if __name__ == "__main__":
    main()

