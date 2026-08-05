# Marketing Response Scenarios V0

This module converts route opportunity scores into scenario-based response curves.

It is not a causal MMM estimate. It is a transparent simulation layer for budget-planning practice.

## Generated Assets

- Curve rows: 336
- Route-scenario summary rows: 42
- Budget unit: CAD
- Response horizon: one annual campaign period

## Top Base-Scenario Route Tests

| Route | Status | Budget | Incremental passenger proxy | Cost / incr. proxy passenger | Health lift pts | Source recommendation |
|---|---|---:|---:|---:|---:|---|
| YKF_YEG | active | $150,000 | 1,121 | $134 | 5.6 | Scale or defend with controlled campaign |
| YXU_YYC | active | $100,000 | 1,805 | $55 | 4.1 | Run test-and-learn marketing |
| YXX_YYC | active | $100,000 | 2,775 | $36 | 4.1 | Run test-and-learn marketing |
| YKF_YYC | active | $100,000 | 2,646 | $38 | 3.4 | Run test-and-learn marketing |
| YLW_YYC | active | $50,000 | 1,005 | $50 | 3.0 | Maintain service; monitor capacity and leakage |
| YKF_YVR | inactive | $75,000 | 1,424 | $53 | 3.0 | Relaunch feasibility test; verify airline capacity first |
| YXU_YVR | inactive | $75,000 | 464 | $162 | 2.7 | Relaunch feasibility test; verify airline capacity first |
| YXX_YEG | active | $50,000 | 1,798 | $28 | 2.6 | Maintain service; monitor capacity and leakage |
| YLW_YVR | active | $50,000 | 9,309 | $5 | 2.4 | Maintain service; monitor capacity and leakage |
| YKF_YHZ | active | $25,000 | 417 | $60 | 2.0 | Watchlist; improve evidence first |

## Scenario Totals at Selected Test Budgets

| Scenario | Selected budget total | Incremental passenger proxy | Mean health lift pts |
|---|---:|---:|---:|
| conservative | $875,000 | 9,607 | 1.7 |
| base | $875,000 | 25,272 | 2.7 |
| optimistic | $875,000 | 55,808 | 4.2 |

## Interpretation Rules

- For active routes, incremental passenger proxy can be interpreted as demand lift under the stated assumptions.
- For inactive routes, incremental passenger proxy is conditional on service being restorable; marketing cannot create passengers without airline capacity.
- Cost per incremental proxy passenger is useful for comparing routes, not for claiming actual CAC.
- These curves are designed to feed Phase 5 budget optimization.
