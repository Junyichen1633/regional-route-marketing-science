"""Probe OpenSky airport arrivals/departures for route-activity feasibility."""

from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "opensky" / "probes"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def ssl_context(allow_insecure_ssl: bool) -> ssl.SSLContext | None:
    if allow_insecure_ssl:
        return ssl._create_unverified_context()
    return None


def build_url(operation: str, airport: str, start: datetime, end: datetime) -> str:
    params = urllib.parse.urlencode(
        {
            "airport": airport,
            "begin": int(start.timestamp()),
            "end": int(end.timestamp()),
        }
    )
    return f"https://opensky-network.org/api/flights/{operation}?{params}"


def fetch_json(url: str, context: ssl.SSLContext | None) -> tuple[int, object]:
    request = urllib.request.Request(url, headers={"User-Agent": "regional-route-ms/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=60, context=context) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        try:
            parsed_payload: object = json.loads(payload)
        except json.JSONDecodeError:
            parsed_payload = payload
        return error.code, parsed_payload


def summarize_flights(flights: object, airport: str, operation: str) -> dict[str, object]:
    if not isinstance(flights, list):
        return {
            "record_count": 0,
            "route_counts": {},
            "airline_callsign_prefixes": {},
        }

    route_counts: dict[str, int] = {}
    callsign_prefixes: dict[str, int] = {}
    for flight in flights:
        if not isinstance(flight, dict):
            continue
        origin = flight.get("estDepartureAirport") or "UNKNOWN"
        destination = flight.get("estArrivalAirport") or "UNKNOWN"
        counterpart = destination if operation == "departure" else origin
        route_key = f"{airport}_{counterpart}"
        route_counts[route_key] = route_counts.get(route_key, 0) + 1

        callsign = str(flight.get("callsign") or "").strip()
        if callsign:
            prefix = "".join(char for char in callsign[:3] if char.isalpha())
            if prefix:
                callsign_prefixes[prefix] = callsign_prefixes.get(prefix, 0) + 1

    return {
        "record_count": len(flights),
        "route_counts": dict(sorted(route_counts.items())),
        "airline_callsign_prefixes": dict(sorted(callsign_prefixes.items())),
    }


def write_outputs(
    *,
    airport: str,
    operation: str,
    date_value: str,
    status: int,
    url: str,
    payload: object,
    summary: dict[str, object],
) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{airport}_{operation}_{date_value}"
    raw_path = RAW_DIR / f"{stem}.json"
    summary_path = OUTPUTS_DIR / f"opensky_probe_{stem}.md"

    raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# OpenSky Probe: {airport} {operation} {date_value}",
        "",
        f"- HTTP status: {status}",
        f"- URL: {url}",
        f"- Records: {summary['record_count']}",
        "",
        "## Route Counts",
        "",
    ]
    route_counts = summary["route_counts"]
    if route_counts:
        lines.extend(["| Route key | Flights |", "|---|---:|"])
        for route_key, count in route_counts.items():
            lines.append(f"| {route_key} | {count} |")
    else:
        lines.append("No route counts available.")

    lines.extend(["", "## Callsign Prefixes", ""])
    prefixes = summary["airline_callsign_prefixes"]
    if prefixes:
        lines.extend(["| Prefix | Flights |", "|---|---:|"])
        for prefix, count in prefixes.items():
            lines.append(f"| {prefix} | {count} |")
    else:
        lines.append("No callsign prefixes available.")

    summary_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--airport", required=True, help="ICAO airport code, e.g. CYKF")
    parser.add_argument("--date", required=True, help="UTC date in YYYY-MM-DD")
    parser.add_argument("--operation", choices=["arrival", "departure"], default="departure")
    parser.add_argument(
        "--allow-insecure-ssl",
        action="store_true",
        help="Disable SSL verification for local environments with broken certificate chains.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = parse_date(args.date)
    end = start + timedelta(days=1)
    context = ssl_context(args.allow_insecure_ssl)
    url = build_url(args.operation, args.airport, start, end)
    status, payload = fetch_json(url, context)
    summary = summarize_flights(payload, args.airport, args.operation)
    write_outputs(
        airport=args.airport,
        operation=args.operation,
        date_value=args.date,
        status=status,
        url=url,
        payload=payload,
        summary=summary,
    )
    print(f"HTTP {status}; records={summary['record_count']}")


if __name__ == "__main__":
    main()

