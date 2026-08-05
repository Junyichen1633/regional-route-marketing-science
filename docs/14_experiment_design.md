# Phase 6 Experiment Design

## Objective

Translate the recommended budget allocation into a validation plan.

This phase answers:

```text
How should the model recommendation be tested before the airport or airline scales spend?
```

## Input

Recommended allocation:

```text
data/processed/budget_optimization_allocations_v0.csv
```

Route opportunity scores:

```text
data/processed/route_opportunity_score_v0.csv
```

Marketing response curves:

```text
data/processed/marketing_response_curve_v0.csv
```

Experiment assumptions:

```text
config/experiment_design_assumptions.csv
```

## Outputs

Route-level experiment plan:

```text
data/processed/experiment_design_plan_v0.csv
```

Matched comparison routes:

```text
data/processed/experiment_control_matches_v0.csv
```

Human-readable outputs:

```text
outputs/experiment_design_v0_summary.md
reports/phase6_experiment_design_memo.md
```

## Recommended Validation Program

The current plan validates:

```text
portfolio_value_500k
```

Scope:

- Funded routes: 7
- Active-route tests: 6
- Relaunch feasibility tests: 1
- Total test budget: CAD 500,000
- Control matches generated: 21

## Test Types

`matched_route_geo_lift`

Used for active scale/defend and test-and-learn routes. The goal is to compare route-level booking or booking-proxy lift against matched comparison routes and/or holdout geographies.

`incrementality_guardrail_test`

Used for maintain routes. The goal is not aggressive scaling; it checks whether small spend protects demand, reduces leakage, or supports retention without harming fare/yield guardrails.

`two_stage_capacity_gated_test`

Used for relaunch routes. The goal is to validate demand signals first, then advance only if airline capacity is plausible.

## Measurement Data Required

Public airport data is not enough for final incrementality measurement.

The real validation layer needs:

- route-level bookings or booking proxy by origin catchment and week
- campaign spend and impressions by route and market
- route page or search conversion events
- load factor or capacity proxy
- fare/yield guardrail if available

## Control Matching

The script selects three comparison routes per treatment route from unfunded routes.

Matching considers:

- route segment
- end-of-period route status
- origin and destination similarity
- distance
- demand context score
- route sustainability score
- marketing support priority score
- competition pressure
- data confidence
- weekly frequency proxy

Controls are not perfect causal controls. They are a practical first design for a portfolio project, and they define where better partner data would be needed.

## Current Route Plan

- `YKF_YEG`: matched-route geo-lift, CAD 100,000.
- `YKF_YYC`: matched-route geo-lift, CAD 100,000.
- `YKF_YVR`: two-stage capacity-gated relaunch test, CAD 75,000.
- `YXU_YYC`: matched-route geo-lift, CAD 75,000.
- `YXX_YYC`: matched-route geo-lift, CAD 75,000.
- `YXX_YEG`: incrementality guardrail test, CAD 50,000.
- `YLW_YVR`: incrementality guardrail test, CAD 25,000.

## Decision Rules

For active routes:

- Scale if observed incremental lift reaches the route-specific success threshold and guardrails hold.
- Maintain or retest if lift is directional but below scale threshold.
- Stop or redesign if lift is weak or guardrails fail.

For relaunch routes:

- Advance only if qualified demand signal reaches threshold and airline capacity partner interest is confirmed.
- Continue validation if demand is promising but below scale threshold.
- Stop if capacity is unavailable or demand signal is weak.

## Next Step

Package the project into a portfolio artifact:

- executive summary
- methodology narrative
- architecture diagram
- key tables
- recommendations
- validation plan
- limitations and next data needs
