# Phase 4 Marketing Response Module

## Objective

Translate route opportunity scores into scenario-based marketing response curves.

This module answers:

```text
If we spend a given campaign budget on a candidate route, what demand lift might we expect under conservative, base, and optimistic assumptions?
```

## Important Positioning

This is not a fitted MMM.

The project does not yet have observed route-level marketing spend or route-level passenger outcomes. Therefore, this phase uses transparent response scenarios, not causal attribution.

The module is still useful because it creates a disciplined bridge between:

- route opportunity scoring
- marketing response assumptions
- budget optimization
- experiment design

## Inputs

Route score input:

```text
data/processed/route_opportunity_score_v0.csv
```

Response assumptions:

```text
config/marketing_response_assumptions.csv
```

## Outputs

Full budget-response curve:

```text
data/processed/marketing_response_curve_v0.csv
```

Selected route-scenario summary:

```text
data/processed/marketing_response_route_summary_v0.csv
```

Human-readable outputs:

```text
outputs/marketing_response_scenarios_v0_summary.md
reports/phase4_marketing_response_memo.md
```

## Response Formula

The v0 response curve uses a diminishing-return function:

```text
incremental passenger proxy = baseline annual passenger proxy
  x adjusted max lift %
  x budget / (budget + half-saturation spend)
  x scenario carryover multiplier
```

The budget-response curve is generated for:

```text
0, 25k, 50k, 75k, 100k, 150k, 250k, 400k CAD
```

## Baseline Passenger Proxy

Because observed route passenger counts are unavailable, the module builds a passenger proxy from:

- direct weekly frequency proxy
- route segment seat assumptions
- two-way annualized capacity approximation
- load factor assumption
- demand context score
- end-of-period route status
- data confidence score

This is intentionally labeled as a proxy.

## Scenario Assumptions

The assumption table defines three scenarios:

- `conservative`: lower lift, slower saturation, lower carryover.
- `base`: central planning case.
- `optimistic`: higher lift, faster saturation, stronger carryover.

Assumptions vary by route segment:

- `short_haul`
- `medium_haul`
- `long_haul`

## Inactive Route Rule

Inactive routes can still appear as high-priority relaunch candidates, but their response is conditional on restored airline capacity.

For these routes:

- `capacity_required_flag = 1`
- half-saturation spend is increased
- max lift is discounted
- interpretation should be feasibility testing, not ordinary always-on media allocation

## Current Readout

In the base scenario, the strongest route tests by route-health lift include:

- `YKF_YEG`: active route, scale/defend candidate
- `YXU_YYC`: active test-and-learn candidate
- `YXX_YYC`: active test-and-learn candidate
- `YKF_YYC`: active test-and-learn candidate with weaker evidence confidence
- `YKF_YVR`: high-priority relaunch feasibility candidate, capacity required

High-volume maintain routes such as `YLW_YVR` can show low cost per incremental proxy passenger because the baseline passenger proxy is large. Phase 5 should therefore include portfolio constraints so the optimizer does not allocate only to already-healthy high-volume routes.

## Next Step

Build a constrained budget optimizer using `marketing_response_curve_v0.csv`.

The optimizer should support:

- total budget constraint
- minimum and maximum spend per route
- route role constraints
- optional relaunch budget bucket
- scenario selection
- objective choice between incremental passenger proxy and route-health lift
