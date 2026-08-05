# Phase 2 Route Supply Layer

## Objective

Create the first route-level supply layer for the MVP route-month panel.

The immediate target is:

```text
route_active
```

This indicates whether a non-stop route appears to be served in a given month based on sourced route events.

## Why This Layer Matters

The project cannot credibly model route sustainability using only airport-level traffic. Route decisions are made at the route level, so the panel needs at least one route-level label.

Because a complete public schedule archive is not currently available, the first route supply layer uses sourced route events:

- Official airport announcements
- Airline announcements
- Schedule archive reporting
- Current schedule aggregators used only as continuity support
- Explicit benchmark or negative-control assumptions

## Core Asset

Manual event source table:

```text
config/route_supply_events.csv
```

Expanded route-month table:

```text
data/processed/route_supply_monthly_v0.csv
```

Enriched model panel:

```text
data/processed/route_month_panel_v2.csv
```

## Event Table Fields

- `route_id`: route identifier from the seed route list
- `event_id`: unique event identifier
- `start_month`: first month covered by the event
- `end_month`: last month covered by the event
- `route_active`: 1 for active, 0 for inactive
- `weekly_frequency_proxy`: approximate weekly frequency if available
- `carrier`: carrier or carriers associated with the event
- `evidence_type`: official release, schedule archive, current schedule support, benchmark assumption, etc.
- `confidence`: high, medium, or low
- `source_title`: source name
- `source_url`: URL or manual assumption marker
- `evidence_note`: short explanation of how the source supports the event

## Coverage

Panel V2 has:

- 1,296 route-month rows
- 894 labeled route-month rows
- 69.0% route-active coverage
- 801 active labels
- 93 inactive labels
- 402 uncovered labels

Uncovered does not mean inactive. It means the project does not yet have enough source evidence for that route-month.

## Modeling Use

Safe first use:

- Train a diagnostic route-active classifier only on labeled rows.
- Treat uncovered rows as missing labels.
- Use airport movement features, route distance, hub competition, seasonality, and COVID/recovery indicators.

Unsafe use:

- Treat uncovered as zero.
- Claim the event table is a complete historical schedule archive.
- Claim weekly frequency proxy is exact observed flight frequency.

## Diagnostic Baseline

The first diagnostic model is:

```text
src/train_route_active_baseline.py
```

It trains a logistic regression model with a temporal split:

- Train: labeled rows from 2020-2024
- Test: labeled rows from 2025

Output:

```text
outputs/route_active_baseline_v0.md
```

This model is a smoke test for panel usefulness. It should not be presented as a final forecasting model because:

- Labels are partially manual and source-driven.
- Positive labels dominate the labeled sample.
- Route identity proxies can inflate apparent performance.
- Some benchmark and negative-control assumptions are structurally easy to classify.

## Next Improvement

Reduce uncovered route-months by adding:

- More historical schedule evidence for YHM, YLW, YXX, and early YKF periods
- Airport annual reports where available
- Airline route announcements
- Schedule archive pages
- Optional paid or authenticated schedule APIs if available

After coverage improves, the project can build:

1. A cleaner route-active model.
2. A route opportunity score.
3. A marketing response simulator.
4. A budget optimizer.

