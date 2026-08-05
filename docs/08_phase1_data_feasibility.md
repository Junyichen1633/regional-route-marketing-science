# Phase 1 Data Feasibility Findings

## Objective

Validate whether public data can support a route-month Marketing Science project for Canadian regional airports.

Target unit:

```text
origin_airport x destination_airport x month
```

Target period:

```text
2020-01 through 2025-12
```

## Main Finding

The fully ideal dataset does not appear publicly available:

```text
route-month passenger demand + route-level marketing spend
```

However, a credible MVP is feasible if we separate the project into:

1. Airport-month supply/activity context from public StatsCan aircraft movements.
2. Route-month structural opportunity panel.
3. Scenario-based marketing response and budget optimization.
4. Explicit experiment design for future causal validation.

## Tested Sources

### Statistics Canada 23-10-0253-01

Air passenger traffic at Canadian airports.

Status: usable for airport-level calibration and hub context.

Result:

- Covers major airports such as YYZ, YVR, YYC, YEG, and YHZ.
- Does not cover several MVP regional airports in the extracted full table.
- Annual frequency only.

Use in project:

- Airport-level demand context.
- Calibration benchmark for major airports.
- Not suitable as route-month outcome.

### Statistics Canada 23-10-0312-01

Screened passenger traffic at the largest airports in Canada.

Status: usable for monthly hub-context features.

Result:

- Provides monthly passenger context for major airports.
- Covers 2020-2025 for hub/context airports in the MVP.
- Not designed for regional airports like YKF, YHM, YXU, YXX, or YLW.

Use in project:

- Destination hub recovery trend.
- Nearest competing hub demand cycle.
- Not suitable as regional route outcome.

### Statistics Canada 23-10-0302-01

Domestic and international itinerant movements by type of operation.

Status: usable for MVP.

Result:

- Covers all 10 MVP airports.
- Provides monthly airport-level movements for 2020-2025.
- Includes domestic movements and air carrier movement categories.
- Does not identify the destination airport for each movement.

Use in project:

- Origin airport supply/activity context.
- Destination airport supply/activity context.
- Nearest competing hub activity context.
- Baseline demand/supply model feature.

Processed asset:

```text
data/processed/statcan_airport_monthly_movements.csv
```

### Statistics Canada 23-10-0304-01

Domestic and international itinerant movements by geography.

Status: rejected for MVP airport modeling.

Result:

- After inspection, the airport dimension only contains:
  - Total, all airports
  - Total, NAV CANADA towers and flight service stations
  - Total, non-NAV CANADA airports
- It does not provide specific airport rows.

Use in project:

- Do not use in the MVP panel.

### OpenSky Airport Flights API

Status: blocked without authentication in current environment.

Probe:

```text
CYKF departures on 2024-07-15
```

Result:

```text
HTTP 403
```

Use in project:

- Keep as an optional future route-level activity source if credentials are available.
- Do not make the MVP dependent on anonymous OpenSky access.

## Current Panel Assets

### Route-Month Skeleton

```text
data/processed/route_month_skeleton.csv
```

- Rows: 1,296
- Routes: 18
- Months: 72

### Panel V1

```text
data/processed/route_month_panel_v1.csv
```

Coverage:

- Origin airport movement features: 100%
- Destination airport movement features: 100%
- Nearest origin hub movement features: 100%
- Observed route passengers: 0%
- Direct route frequency: 0%

## Decision

Proceed with the project, but define the first modeling target carefully.

Do not claim:

```text
We model observed route-month passenger demand.
```

Instead, use:

```text
We model route opportunity and route sustainability using airport-month supply/activity context, structural route features, and scenario-based marketing response.
```

The next data milestone is to add one of the following route-level labels:

- Route active status by month.
- Direct flight frequency by route-month.
- Estimated seats by route-month.
- Manually validated route history for a smaller route set.

## Recommended Next Step

Build a route-level supply layer:

1. Search for public airport or airline route schedule archives.
2. If no robust source exists, create a manually validated route-active table for the MVP route set.
3. Use `route_active` as the first supervised target.
4. Use airport movements, hub competition, distance, seasonality, and COVID/recovery period as predictors.

