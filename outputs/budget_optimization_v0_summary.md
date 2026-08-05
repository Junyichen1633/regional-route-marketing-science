# Budget Optimization V0

This optimizer selects one budget level per route from `marketing_response_curve_v0.csv` under portfolio constraints.

The solver is a deterministic dynamic program over CAD 25,000 budget increments. No external optimization package is required.

## Case Summary

| Case | Scenario | Objective | Budget | Allocated | Routes | Relaunch budget | Incr. passenger proxy | Health lift pts | Cost / incr. proxy passenger |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| pilot_health_250k | base | route_health | $250,000 | $250,000 | 4 | $0 | 4,550 | 13.8 | $55 |
| balanced_health_500k | base | route_health | $500,000 | $500,000 | 7 | $0 | 18,081 | 24.5 | $28 |
| growth_passengers_500k | base | incremental_passengers | $500,000 | $500,000 | 6 | $0 | 23,734 | 17.4 | $21 |
| portfolio_value_500k | base | portfolio_value | $500,000 | $500,000 | 7 | $75,000 | 16,936 | 22.2 | $30 |
| downside_portfolio_500k | conservative | portfolio_value | $500,000 | $500,000 | 7 | $50,000 | 7,970 | 14.3 | $63 |
| upside_portfolio_500k | optimistic | portfolio_value | $500,000 | $500,000 | 7 | $75,000 | 37,855 | 34.8 | $13 |
| broad_test_875k | base | portfolio_value | $875,000 | $875,000 | 10 | $150,000 | 24,539 | 36.2 | $36 |

## Recommended Case: `portfolio_value_500k`

| Route | Budget | Bucket | Incr. passenger proxy | Health lift pts | Recommendation |
|---|---:|---|---:|---:|---|
| YKF_YEG | $100,000 | scale_defend | 917 | 4.5 | Scale or defend with controlled campaign |
| YKF_YYC | $100,000 | test_and_learn | 2,646 | 3.4 | Run test-and-learn marketing |
| YKF_YVR | $75,000 | relaunch_feasibility | 1,424 | 3.0 | Relaunch feasibility test; verify airline capacity first |
| YXU_YYC | $75,000 | test_and_learn | 1,527 | 3.5 | Run test-and-learn marketing |
| YXX_YYC | $75,000 | test_and_learn | 2,417 | 3.6 | Run test-and-learn marketing |
| YXX_YEG | $50,000 | maintain | 1,798 | 2.6 | Maintain service; monitor capacity and leakage |
| YLW_YVR | $25,000 | maintain | 6,206 | 1.6 | Maintain service; monitor capacity and leakage |

## Interpretation

- `portfolio_value_500k` is the recommended planning case because it balances route-health lift, passenger proxy, and strategic priority.
- `growth_passengers_500k` shows what happens when the objective is pure passenger proxy; this is useful but can overweight already-healthy high-volume routes.
- Relaunch candidates are capped separately because marketing cannot create demand without restored airline capacity.
- The optimizer is only as credible as the response assumptions from Phase 4.
