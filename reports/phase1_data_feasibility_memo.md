# Phase 1 Memo: Data Feasibility and Modeling Implications

## Executive Summary

The ideal project dataset would contain route-month passengers, route-level flight frequency, fare/yield, and observed marketing spend. Public data does not appear to fully support that ideal structure for Canadian domestic regional routes.

The project is still feasible as a strong L4 Product Data Scientist portfolio project if it is framed correctly:

> Build a route investment decision system using public airport activity data, route structure, hub competition, and scenario-based marketing response.

The first model should not claim to estimate true route-month passenger demand. It should estimate route opportunity and sustainability, then use a separate marketing response simulator and experiment plan for investment decisions.

## What We Found

### Strong Public Data

Statistics Canada Table 23-10-0302-01 provides monthly airport-level aircraft movements for all MVP airports:

- YKF
- YHM
- YXU
- YXX
- YLW
- YVR
- YYZ
- YYC
- YEG
- YHZ

This creates a credible public-data backbone for airport-month supply/activity context.

### Partial Public Data

Statistics Canada Table 23-10-0253-01 provides annual airport passenger traffic for major airports. It is useful for hub calibration but not enough for regional route-month modeling.

Statistics Canada Table 23-10-0312-01 provides monthly screened passenger traffic for major airports. It is useful for YYZ/YVR/YYC/YEG/YHZ demand cycle context, not for regional airports.

### Blocked or Weak Public Data

OpenSky's airport flight endpoint returned HTTP 403 in a CYKF probe, so anonymous access should not be treated as a dependable route-level data source.

Statistics Canada Table 23-10-0304-01 was rejected because it does not provide specific airport rows.

## Modeling Implication

The first modeling target should be one of:

- `route_active`
- `route_opportunity_score`
- `route_sustainability_score`
- `flight_frequency_proxy`, if route-level schedule data becomes available

Avoid presenting the MVP as:

> Predicting true monthly route passengers.

Use this instead:

> Estimating route opportunity and investment priority under public-data constraints.

## Current Data Asset

The project now has a first enriched route-month panel:

```text
data/processed/route_month_panel_v1.csv
```

It contains:

- 18 seed routes
- 72 months
- 1,296 route-month rows
- 100% coverage for origin airport movement context
- 100% coverage for destination airport movement context
- 100% coverage for nearest competing hub movement context

It does not yet contain:

- Observed route passengers
- Direct route frequency
- Observed marketing spend

## Recommendation

Proceed to Phase 2 with a route-level supply layer.

Best next step:

Create a route-active history for the MVP routes from public schedules, route announcements, airport annual reports, or a small manually validated source table.

Once `route_active` exists, the project can build:

1. Baseline route opportunity model
2. Marketing response simulator
3. Budget optimization layer
4. Experiment design recommendation

