# Phase 3 Memo: Route Opportunity Score V0

## Business Question

Which regional Canadian air routes look most worth supporting with marketing, given public airport activity data, sourced route supply signals, and nearby hub competition?

## Current Answer

The v0 score produces a target-route ranking that separates three ideas:

- Sustainability: whether the route appears operationally viable before marketing.
- Marketing support priority: whether limited budget should be tested or defended on the route.
- Evidence quality: whether the decision has enough sourced schedule coverage to be credible.

## Top Target Routes

| Rank | Route | End status | Priority | Sustainability | Active rate 2023-2025 | Data confidence | Recommendation |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | YKF_YVR | inactive | 81.9 | 76.7 | 91.7% | 99.5 | Relaunch feasibility test; verify airline capacity first |
| 2 | YKF_YEG | active | 71.6 | 73.3 | 58.3% | 93.9 | Scale or defend with controlled campaign |
| 3 | YKF_YYC | active | 68.1 | 76.3 | 100.0% | 52.1 | Run test-and-learn marketing |
| 4 | YXU_YVR | inactive | 67.4 | 68.8 | 90.3% | 81.4 | Relaunch feasibility test; verify airline capacity first |
| 5 | YXX_YYC | active | 65.9 | 77.5 | 100.0% | 93.8 | Run test-and-learn marketing |

## Interpretation

High priority routes are not automatically the largest routes. They are routes where regional strategic value, demand context, hub leakage pressure, service gaps, and evidence quality line up.

Hub-to-hub routes are retained as benchmarks, not as candidates for regional marketing allocation. The local YXX-YVR route is retained as a negative/control route because its value proposition is structurally different from longer regional-to-hub access routes.

## Limitations

- No route-month passenger demand is observed yet.
- `direct_weekly_frequency_proxy` is event-based and incomplete.
- The score is heuristic, so it should be challenged with sensitivity analysis.
- Marketing effects are not estimated in this phase.

## Next Step

Build a marketing response scenario module that converts budget into incremental passenger or route-health lift under conservative, base, and optimistic assumptions.
