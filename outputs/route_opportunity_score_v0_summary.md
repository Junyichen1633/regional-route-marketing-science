# Route Opportunity Score V0

This file summarizes a transparent route-level scoring layer built from `route_month_panel_v2.csv`.

The score is a decision-support baseline, not a causal MMM estimate.

## Scope

- Analysis window: 2023-2025
- Routes scored: 18
- Target regional routes: 14
- Benchmark routes: 3
- Negative/control routes: 1

## Score Components

- `service_viability_score`: route-active continuity, recent 2025 activity, frequency proxy, and label coverage.
- `demand_context_score`: origin airport movement scale, destination movement scale, destination screened passengers, and nearby hub demand context.
- `regional_strategic_fit_score`: business fit for regional airport support, with hub-to-hub routes treated as benchmarks.
- `competition_pressure_score`: nearby hub activity adjusted by distance from the origin airport.
- `data_confidence_score`: route label coverage plus source confidence.

## Top Target Routes by Marketing Support Priority

| Rank | Route | End status | Priority | Sustainability | Active rate 2023-2025 | Data confidence | Recommendation |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | YKF_YVR | inactive | 81.9 | 76.7 | 91.7% | 99.5 | Relaunch feasibility test; verify airline capacity first |
| 2 | YKF_YEG | active | 71.6 | 73.3 | 58.3% | 93.9 | Scale or defend with controlled campaign |
| 3 | YKF_YYC | active | 68.1 | 76.3 | 100.0% | 52.1 | Run test-and-learn marketing |
| 4 | YXU_YVR | inactive | 67.4 | 68.8 | 90.3% | 81.4 | Relaunch feasibility test; verify airline capacity first |
| 5 | YXX_YYC | active | 65.9 | 77.5 | 100.0% | 93.8 | Run test-and-learn marketing |
| 6 | YXU_YYC | active | 63.4 | 80.8 | 100.0% | 100.0 | Run test-and-learn marketing |
| 7 | YKF_YHZ | active | 59.5 | 68.0 | 100.0% | 100.0 | Watchlist; improve evidence first |
| 8 | YXX_YEG | active | 58.7 | 71.6 | 100.0% | 93.8 | Maintain service; monitor capacity and leakage |
| 9 | YHM_YEG | active | 58.4 | 63.8 | 100.0% | 47.2 | Watchlist; improve evidence first |
| 10 | YLW_YYC | active | 56.9 | 81.4 | 100.0% | 93.8 | Maintain service; monitor capacity and leakage |

## Benchmarks and Controls

| Rank | Route | End status | Priority | Sustainability | Active rate 2023-2025 | Data confidence | Recommendation |
|---:|---|---|---:|---:|---:|---:|---|
|  | YVR_YYC | active | 0.0 | 64.2 | 100.0% | 93.8 | Benchmark only; exclude from regional marketing allocation |
|  | YYZ_YVR | active | 0.0 | 70.7 | 100.0% | 93.8 | Benchmark only; exclude from regional marketing allocation |
|  | YYZ_YYC | active | 0.0 | 67.4 | 100.0% | 93.8 | Benchmark only; exclude from regional marketing allocation |
|  | YXX_YVR | inactive | 0.0 | 35.7 | 0.0% | 93.8 | Control route; do not prioritize |

## Formula Notes

`route_sustainability_score_v0` rewards end-of-period service status, recent activity, demand context, strategic fit, and data confidence, then penalizes nearby hub competition pressure.

`marketing_support_priority_score_v0` is only assigned to target regional routes. It rewards demand context, strategic fit, hub-leakage pressure, service gaps, and data confidence.

Because route-level passenger demand and true marketing spend are not observed yet, these scores should be interpreted as a portfolio triage tool.
