"""Inspect StatsCan airport passenger traffic coverage for MVP airports."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
RAW_STATCAN_DIR = PROJECT_ROOT / "data" / "raw" / "statcan" / "23100253"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DATA_FILE = RAW_STATCAN_DIR / "23100253.csv"


def load_airports() -> dict[str, str]:
    with (CONFIG_DIR / "airports.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {row["iata"]: row["name"] for row in reader}


def normalize(value: str) -> str:
    return " ".join(value.lower().replace("/", " ").replace("-", " ").split())


def find_airport_iata(geo: str, airport_names: dict[str, str]) -> str | None:
    normalized_geo = normalize(geo)
    for iata, name in airport_names.items():
        normalized_name = normalize(name)
        name_tokens = normalized_name.split()
        if normalized_name in normalized_geo:
            return iata
        if len(name_tokens) >= 2 and all(token in normalized_geo for token in name_tokens[:2]):
            return iata
    return None


def inspect_rows(airport_names: dict[str, str]) -> dict[str, dict[str, object]]:
    coverage: dict[str, dict[str, object]] = {
        iata: {
            "airport_name": name,
            "matched_geos": set(),
            "years": set(),
            "traffic_categories": set(),
            "row_count": 0,
        }
        for iata, name in airport_names.items()
    }

    with DATA_FILE.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            iata = find_airport_iata(row["GEO"], airport_names)
            if iata is None:
                continue
            coverage[iata]["matched_geos"].add(row["GEO"])
            coverage[iata]["years"].add(row["REF_DATE"])
            coverage[iata]["traffic_categories"].add(row["Air passenger traffic"])
            coverage[iata]["row_count"] += 1
    return coverage


def write_summary(coverage: dict[str, dict[str, object]]) -> None:
    lines = [
        "# StatsCan Airport Traffic Coverage",
        "",
        "Source: Statistics Canada Table 23-10-0253-01, full-table CSV download.",
        "",
        "| IATA | Rows | Years | Matched geography | Traffic categories |",
        "|---|---:|---|---|---|",
    ]

    for iata, info in sorted(coverage.items()):
        years = sorted(info["years"])
        geos = sorted(info["matched_geos"])
        categories = sorted(info["traffic_categories"])
        years_text = f"{years[0]}-{years[-1]}" if years else "not found"
        geos_text = "<br>".join(geos) if geos else "not found"
        categories_text = "<br>".join(categories) if categories else "not found"
        lines.append(
            f"| {iata} | {info['row_count']} | {years_text} | {geos_text} | {categories_text} |"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- This table is useful for airport-level context and calibration.",
            "- It does not provide route-month passenger demand.",
            "- Missing regional airports here would strengthen the case for using flight supply proxies.",
            "",
        ]
    )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "statcan_airport_traffic_coverage.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing {DATA_FILE}")
    airport_names = load_airports()
    coverage = inspect_rows(airport_names)
    write_summary(coverage)
    found = sum(1 for info in coverage.values() if info["row_count"] > 0)
    print(f"Found coverage for {found} of {len(coverage)} MVP airports.")


if __name__ == "__main__":
    main()

