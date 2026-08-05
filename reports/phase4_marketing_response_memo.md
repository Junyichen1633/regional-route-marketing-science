# Phase 4 Memo: Marketing Response Scenarios V0

## Business Question

If a regional airport had limited marketing funds, how much incremental route demand might different candidate routes generate under conservative, base, and optimistic response assumptions?

## Method

This phase uses a diminishing-return response curve rather than a fitted MMM:

```text
incremental passenger proxy = baseline annual passenger proxy
  x adjusted max lift %
  x budget / (budget + half-saturation spend)
  x scenario carryover multiplier
```

The baseline passenger proxy is capacity-and-demand scaled. It starts from route frequency, aircraft-seat assumptions, and load factor, then adjusts for demand context, route status, and evidence confidence.

## Base Scenario Readout

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

## Key Caveat

Inactive-route rows are relaunch scenarios. Their response is conditional on restored airline capacity, so they should be treated as feasibility-test candidates rather than normal media-allocation candidates.

## Next Step

Use the response curve table to build a constrained budget optimizer that selects route-budget pairs under a fixed total budget.
