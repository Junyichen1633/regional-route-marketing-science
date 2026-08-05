# Phase 5 Memo: Budget Optimization V0

## Business Question

Given a fixed regional route marketing budget, which route-budget pairs should be funded under realistic portfolio constraints?

## Recommended Planning Case

The recommended v0 case is `portfolio_value_500k`.

- Total budget: $500,000
- Allocated budget: $500,000
- Funded routes: 7
- Relaunch budget: $75,000
- Incremental passenger proxy: 16,936
- Incremental route-health lift: 22.2 points
- Cost per incremental proxy passenger: $30

## Recommended Allocation

| Route | Budget | Bucket | Incr. passenger proxy | Health lift pts | Recommendation |
|---|---:|---|---:|---:|---|
| YKF_YEG | $100,000 | scale_defend | 917 | 4.5 | Scale or defend with controlled campaign |
| YKF_YYC | $100,000 | test_and_learn | 2,646 | 3.4 | Run test-and-learn marketing |
| YKF_YVR | $75,000 | relaunch_feasibility | 1,424 | 3.0 | Relaunch feasibility test; verify airline capacity first |
| YXU_YYC | $75,000 | test_and_learn | 1,527 | 3.5 | Run test-and-learn marketing |
| YXX_YYC | $75,000 | test_and_learn | 2,417 | 3.6 | Run test-and-learn marketing |
| YXX_YEG | $50,000 | maintain | 1,798 | 2.6 | Maintain service; monitor capacity and leakage |
| YLW_YVR | $25,000 | maintain | 6,206 | 1.6 | Maintain service; monitor capacity and leakage |

## Why This Is Useful

The optimizer makes the tradeoff explicit: a passenger-maximizing objective, a health-lift objective, and a balanced portfolio objective can recommend different allocations. This is the kind of business-facing modeling decision a product data scientist should be able to explain.

## Guardrails

- Treat all passenger results as proxy outcomes, not observed passengers.
- Keep relaunch allocations in a separate bucket until airline capacity is confirmed.
- Do not use this as a media plan without validating route-level spend and passenger outcomes.

## Next Step

Design an experiment plan for the recommended active-route tests and relaunch feasibility candidates.
