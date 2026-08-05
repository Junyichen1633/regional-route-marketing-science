# Phase 5 Budget Optimization

## Objective

Select route-budget pairs under a fixed marketing budget.

This module answers:

```text
Given a budget constraint and route-level response curves, which routes should receive marketing support and how much should each receive?
```

## Input

Budget-response curve:

```text
data/processed/marketing_response_curve_v0.csv
```

Optimization case definitions:

```text
config/budget_optimizer_cases.csv
```

## Outputs

Case-level summary:

```text
data/processed/budget_optimization_case_summary_v0.csv
```

Route-level allocation output:

```text
data/processed/budget_optimization_allocations_v0.csv
```

Human-readable outputs:

```text
outputs/budget_optimization_v0_summary.md
reports/phase5_budget_optimization_memo.md
```

## Solver

The v0 optimizer uses deterministic dynamic programming over CAD 25,000 budget increments.

For each route, it selects one budget level from the response curve:

```text
0, 25k, 50k, 75k, 100k, 150k, 250k, 400k CAD
```

The optimizer enforces:

- total budget limit
- maximum budget per route
- maximum funded route count
- minimum active-route funded count
- relaunch eligibility
- maximum relaunch budget

No external optimization package is required.

## Objectives

The optimizer compares three objective types:

- `route_health`: maximize incremental route-health lift.
- `incremental_passengers`: maximize incremental passenger proxy.
- `portfolio_value`: balance route-health lift, incremental passenger proxy, and strategic priority.

`portfolio_value` is the recommended planning objective because it avoids treating the problem as pure passenger volume maximization.

## Current Optimization Cases

The v0 run includes:

- `pilot_health_250k`
- `balanced_health_500k`
- `growth_passengers_500k`
- `portfolio_value_500k`
- `downside_portfolio_500k`
- `upside_portfolio_500k`
- `broad_test_875k`

## Recommended Planning Case

The current recommended case is:

```text
portfolio_value_500k
```

Summary:

- Total budget: CAD 500,000
- Allocated budget: CAD 500,000
- Funded routes: 7
- Relaunch budget: CAD 75,000
- Incremental passenger proxy: 16,936
- Incremental route-health lift: 22.2 points
- Cost per incremental proxy passenger: CAD 30

Recommended allocation:

- `YKF_YEG`: CAD 100,000, scale/defend
- `YKF_YYC`: CAD 100,000, test-and-learn
- `YKF_YVR`: CAD 75,000, relaunch feasibility
- `YXU_YYC`: CAD 75,000, test-and-learn
- `YXX_YYC`: CAD 75,000, test-and-learn
- `YXX_YEG`: CAD 50,000, maintain
- `YLW_YVR`: CAD 25,000, maintain

## Interpretation

This phase is useful because it makes tradeoffs explicit.

A passenger-maximizing plan can over-allocate to already-healthy high-volume routes. A route-health objective can overemphasize routes where marketing is not the primary bottleneck. The balanced portfolio objective is a cleaner executive narrative because it connects the model to the business decision.

## Limitations

- Incremental passengers are proxy outcomes, not observed passenger counts.
- Response curves are scenario-based, not fitted causal effects.
- Relaunch routes still require airline capacity confirmation.
- The optimizer assumes budget options are independent across routes.

## Next Step

Design an experiment plan for the recommended allocation.

The experiment plan should specify:

- treatment routes
- holdout or matched comparison routes
- success metrics
- campaign timing
- minimum detectable effect
- decision rules for scale, maintain, or stop
