"""Build the first route-month panel skeleton.

This script intentionally uses only the Python standard library so the first
project iteration can run without installing dependencies.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

START_YEAR = 2020
END_YEAR = 2025


@dataclass(frozen=True)
class Airport:
    iata: str
    icao: str
    name: str
    city: str
    province: str
    country: str
    latitude: float
    longitude: float
    airport_role: str
    notes: str


def read_airports(path: Path) -> dict[str, Airport]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        airports = {}
        for row in reader:
            airport = Airport(
                iata=row["iata"],
                icao=row["icao"],
                name=row["name"],
                city=row["city"],
                province=row["province"],
                country=row["country"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                airport_role=row["airport_role"],
                notes=row["notes"],
            )
            airports[airport.iata] = airport
    return airports


def read_routes(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def month_range(start_year: int, end_year: int) -> list[date]:
    months = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            months.append(date(year, month, 1))
    return months


def covid_period(year: int, month: int) -> str:
    if year == 2020:
        return "covid_shock"
    if year == 2021:
        return "covid_restriction"
    if year == 2022:
        return "recovery"
    return "post_recovery"


def season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "fall"


def nearest_hub(origin: Airport, airports: dict[str, Airport]) -> tuple[str, float]:
    hubs = [airport for airport in airports.values() if airport.airport_role == "hub"]
    nearest = min(
        hubs,
        key=lambda hub: haversine_km(
            origin.latitude,
            origin.longitude,
            hub.latitude,
            hub.longitude,
        ),
    )
    distance = haversine_km(
        origin.latitude,
        origin.longitude,
        nearest.latitude,
        nearest.longitude,
    )
    return nearest.iata, distance


def route_segment(distance_km: float) -> str:
    if distance_km < 300:
        return "short_haul"
    if distance_km < 1500:
        return "medium_haul"
    return "long_haul"


def build_panel(
    airports: dict[str, Airport],
    routes: list[dict[str, str]],
    months: list[date],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for route in routes:
        origin = airports[route["origin_iata"]]
        destination = airports[route["destination_iata"]]
        distance = haversine_km(
            origin.latitude,
            origin.longitude,
            destination.latitude,
            destination.longitude,
        )
        nearest_hub_iata, nearest_hub_distance = nearest_hub(origin, airports)
        is_regional_origin = origin.airport_role == "regional"
        is_hub_destination = destination.airport_role == "hub"

        for month_start in months:
            month_num = month_start.month
            rows.append(
                {
                    "route_id": route["route_id"],
                    "origin_iata": origin.iata,
                    "destination_iata": destination.iata,
                    "origin_city": origin.city,
                    "destination_city": destination.city,
                    "origin_province": origin.province,
                    "destination_province": destination.province,
                    "month": month_start.isoformat(),
                    "year": month_start.year,
                    "month_num": month_num,
                    "quarter": (month_num - 1) // 3 + 1,
                    "season": season(month_num),
                    "covid_period": covid_period(month_start.year, month_num),
                    "is_peak_travel_month": int(month_num in (3, 6, 7, 8, 12)),
                    "route_group": route["route_group"],
                    "strategic_role": route["strategic_role"],
                    "status_assumption": route["status_assumption"],
                    "is_regional_origin": int(is_regional_origin),
                    "is_hub_destination": int(is_hub_destination),
                    "distance_km": round(distance, 1),
                    "route_segment": route_segment(distance),
                    "nearest_origin_hub_iata": nearest_hub_iata,
                    "nearest_origin_hub_distance_km": round(nearest_hub_distance, 1),
                    "notes": route["notes"],
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No rows to write.")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    route_count = len({row["route_id"] for row in rows})
    month_count = len({row["month"] for row in rows})
    regional_target_rows = sum(
        1 for row in rows if row["is_regional_origin"] == 1 and row["route_group"] != "hub_to_hub"
    )
    route_segments = sorted({str(row["route_segment"]) for row in rows})

    content = [
        "# Route-Month Skeleton Summary",
        "",
        f"- Rows: {len(rows):,}",
        f"- Routes: {route_count:,}",
        f"- Months: {month_count:,}",
        f"- Date range: {START_YEAR}-01 to {END_YEAR}-12",
        f"- Regional target rows: {regional_target_rows:,}",
        f"- Route segments: {', '.join(route_segments)}",
        "",
        "This is a structural panel skeleton. It does not yet contain observed passenger demand, flight frequency, weather, holidays, or marketing variables.",
        "",
    ]
    path.write_text("\n".join(content), encoding="utf-8")


def main() -> None:
    airports = read_airports(CONFIG_DIR / "airports.csv")
    routes = read_routes(CONFIG_DIR / "seed_routes.csv")
    months = month_range(START_YEAR, END_YEAR)
    rows = build_panel(airports, routes, months)

    write_csv(DATA_PROCESSED_DIR / "route_month_skeleton.csv", rows)
    write_summary(OUTPUTS_DIR / "route_month_skeleton_summary.md", rows)
    print(f"Wrote {len(rows):,} rows for {len(routes):,} routes.")


if __name__ == "__main__":
    main()

