# Phase 3 Route Opportunity Score

## Objective

Create a route-level decision layer that ranks candidate regional routes before any marketing response or budget optimization is added.

This score answers:

```text
Given the current public-data panel, which regional routes look most worth marketing support, further validation, or relaunch testing?
```

## Input

Primary input:

```text
data/processed/route_month_panel_v2.csv
```

The v0 score uses the 2023-2025 period because it is closer to post-pandemic market behavior than 2020-2022.

## Output

Generated route-level output:

```text
data/processed/route_opportunity_score_v0.csv
```

Human-readable outputs:

```text
outputs/route_opportunity_score_v0_summary.md
reports/phase3_route_opportunity_memo.md
```

## Route Roles

Routes are split into three modeling roles:

- `target`: regional routes eligible for marketing support ranking.
- `benchmark`: hub-to-hub routes retained for scale comparison, not budget allocation.
- `negative_control`: structurally different or intentionally inactive routes used as controls.

## Score Components

`service_viability_score` rewards:

- end-of-period route status
- 2025 route-active rate
- 2023-2025 route-active rate
- direct weekly frequency proxy
- route label coverage

`demand_context_score` rewards:

- origin airport domestic air-carrier movement scale
- destination airport domestic air-carrier movement scale
- destination screened passenger volume
- nearby hub demand context

`regional_strategic_fit_score` encodes the business value of regional connectivity. Long-haul regional routes receive the strongest fit score, hub-to-hub benchmarks receive low fit, and the negative-control route receives zero.

`competition_pressure_score` measures nearby hub pressure using hub domestic air-carrier movements adjusted by distance from the regional origin. This is treated as a sustainability risk but also a reason marketing might matter if the route is otherwise plausible.

`data_confidence_score` combines route-active label coverage with source confidence.

## Composite Scores

`route_sustainability_score_v0` rewards service viability, demand context, strategic fit, and data confidence, then penalizes nearby hub competition pressure.

`marketing_support_priority_score_v0` is assigned only to target regional routes. It rewards demand context, strategic fit, hub-leakage pressure, service gaps, and data confidence.

## Interpretation

The score is a portfolio triage layer, not a causal model.

Good uses:

- Rank routes for follow-up analysis.
- Identify routes that need schedule-data improvement.
- Separate relaunch candidates from active-route marketing candidates.
- Provide an interpretable baseline before adding MMM or optimization.

Bad uses:

- Claim true marketing ROI.
- Treat synthetic spend as observed spend.
- Treat uncovered route-months as inactive.
- Treat event-based frequency proxy as exact schedule frequency.

## Current Readout

The first v0 ranking identifies:

- `YKF_YVR` as a high-priority relaunch feasibility candidate because demand context and strategic fit are strong, but end-of-period status is inactive.
- `YKF_YEG`, `YKF_YYC`, `YXX_YYC`, and `YXU_YYC` as active-route candidates for controlled marketing tests or defend/scale decisions.
- Hub-to-hub routes as benchmarks only.
- `YXX_YVR` as a control route, not a marketing allocation target.

## Next Step

Add a marketing response scenario module that converts route budget into incremental passengers or route-health lift under conservative, base, and optimistic assumptions.
