# Phase 2 Memo: Route Supply Layer

## Executive Summary

The project now has a first sourced route-active layer. This is the bridge between airport-level public data and the route-level business decision.

The new panel, `route_month_panel_v2.csv`, contains route-active labels for 69.0% of route-months. Unlabeled months remain explicitly uncovered, rather than being treated as inactive.

## What Changed

Added:

- Sourced route supply event table
- Monthly route supply expansion script
- Panel V2 with route-active and weekly-frequency proxy fields
- Diagnostic route-active baseline model

## Why This Is Useful

The first phase proved that route-month passenger volume is not easily available from public data. Phase 2 gives the project a practical route-level target:

```text
Is this non-stop route active in this month?
```

This can support:

- Route opportunity modeling
- Route discontinuation risk analysis
- Marketing investment eligibility rules
- Scenario planning for routes with weak or unstable service

## Current Limitation

The route-active labels are not a complete schedule archive. They are assembled from official announcements, airline releases, schedule archives, current schedule support, and explicit assumptions.

This is acceptable for the MVP if the limitation is documented and the next iteration improves coverage.

## Diagnostic Model

A first logistic regression baseline was trained on labeled rows only:

- Train period: 2020-2024
- Test period: 2025
- Test ROC AUC: 0.851

This should be interpreted as a diagnostic that the panel contains signal, not as final model performance.

## Recommendation

Proceed to a route opportunity score next.

Before a polished final model, improve route-active label coverage for:

- YHM to YYC/YVR early years
- YLW to YYC/YEG early years
- YXX to YYC early years
- YKF to YYC continuity between 2021 and 2024

