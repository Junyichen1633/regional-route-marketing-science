# Phase 7 Portfolio Packaging

## Objective

Package the project into artifacts that are easy for a business or technical reviewer to evaluate.

This phase answers:

```text
How do we turn the modeling workflow into a clear portfolio story?
```

## Inputs

The portfolio builder reads the project outputs from earlier phases:

```text
data/processed/route_opportunity_score_v0.csv
data/processed/marketing_sensitivity_summary_v0.csv
data/processed/budget_optimization_case_summary_v0.csv
data/processed/budget_optimization_allocations_v0.csv
data/processed/experiment_design_plan_v0.csv
```

## Script

```text
src/build_portfolio_artifacts.py
```

## Outputs

Final portfolio case study:

```text
reports/final_portfolio_case_study.md
```

Short snapshot:

```text
outputs/final_portfolio_snapshot.md
```

## What The Case Study Emphasizes

- The business decision, not just the model.
- MMM as a component, not the entire project.
- Public-data limitations and proxy outcome labeling.
- Route opportunity scoring.
- Marketing response scenarios.
- Sensitivity and recovery analysis for simulated marketing data.
- Budget optimization under portfolio constraints.
- Experiment design before scaling spend.
- Vertex AI and Meridian as a future production path when real spend and booking data exist.

## Main Portfolio Claim

The project supports:

```text
route-level portfolio direction and experiment prioritization under public-data constraints
```

The project does not claim:

```text
observed causal channel ROI
```

## Recommended Presentation Framing

Lead with the decision:

```text
Which regional routes should receive marketing support, how much should each receive, and how should the recommendation be validated?
```

Then explain the project flow:

```text
data feasibility -> route-month panel -> route opportunity score -> response scenarios
-> sensitivity/recovery analysis -> budget optimization -> experiment design
```

The strongest maturity signal is the sensitivity layer:

```text
Budget direction is more stable than exact channel ranking.
```

This shows that the project understands the limits of simulated marketing data.
