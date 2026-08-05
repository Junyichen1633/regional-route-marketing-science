
# Regional Air Route Marketing Science

## Personal Motivation

This project began with a personal travel problem.

While studying at the University of Waterloo, I frequently traveled between Waterloo and Vancouver. For a period of time, Flair Airlines operated a direct and relatively affordable route between Waterloo International Airport (YKF) and Vancouver International Airport (YVR), which made the trip much more convenient than traveling through Toronto Pearson.

When that route was discontinued, my travel became more expensive, less direct, and more time-consuming. This made me curious about a simple question:

> Why do regional air routes disappear, even when they appear valuable to local travelers?

At first, I assumed the answer was only weak passenger demand. However, route sustainability depends on a broader set of factors, including flight frequency, competition from nearby hub airports, seasonality, operating economics, network strategy, and passenger awareness.

That led to a larger and more actionable question:

If regional airports and airlines have limited marketing resources, which routes are worth supporting, and where can incremental marketing realistically improve route sustainability?

The YKF–YVR route is therefore the motivation for the project, not a case where this analysis claims to reconstruct Flair Airlines’ internal decision. The project expands from one personal travel disruption into a broader Marketing Science decision framework for Canadian regional airports.

## Project Thesis

This project studies how Canadian regional airports can make better route-support decisions when marketing budgets are limited.

The core business question is:

> Which regional air routes should receive incremental marketing investment, and how should a fixed budget be allocated to maximize sustainable demand?

This is not positioned as a pure Marketing Mix Modeling project. MMM is one component inside a broader Marketing Science decision-support system.

## Decision Framework

The project has three modeling layers:

1. Route Demand and Supply Model
   - Estimate baseline route demand or route activity.
   - Separate structural drivers from marketing-driven demand.
   - Examples: seasonality, flight frequency, airport competition, holidays, weather, macroeconomic conditions.

2. Marketing Response Model
   - Estimate or simulate how incremental marketing affects route demand.
   - Use adstock, saturation, and response curves.
   - Google Meridian is the preferred MMM framework when the data supports it.
   - If real spend is unavailable, marketing investment must be treated as scenario-based simulation rather than observed causal attribution.

3. Budget Optimization
   - Allocate a fixed marketing budget across candidate routes.
   - Compare objectives such as incremental passengers, contribution margin, route sustainability score, and marginal ROI.
   - Recommend where to invest, where to hold, and where marketing is unlikely to change the business outcome.


## Key Constraint

Real airline or airport marketing spend is usually proprietary. Any synthetic marketing spend must be labeled as simulated. The project should avoid claiming true causal marketing attribution unless calibrated by real experiments or credible observed spend data.

## Initial Folder Structure

- `docs/`: project design, foundations, data strategy, decision memos
- `data/raw/`: downloaded or manually exported raw public data
- `data/processed/`: cleaned route-month panel datasets
- `notebooks/`: EDA and model exploration
- `src/`: reusable data, modeling, and optimization code
- `reports/`: executive writeups and portfolio narrative
- `outputs/`: figures, tables, model artifacts

## Current Build Status

Current implemented layers:

- Route-month panel skeleton for 18 routes across 2020-2025.
- Statistics Canada airport demand and movement context.
- Sourced route-active supply layer.
- Diagnostic route-active baseline classifier.
- Route opportunity score v0 for regional marketing triage.
- Scenario-based marketing response curves for conservative/base/optimistic assumptions.
- Marketing sensitivity and recovery analysis for simulated channel effects.
- Constrained budget optimization across route-budget pairs.
- Experiment design layer for validating the recommended allocation.
- Final portfolio case study and Chinese interview talk track.
- Standalone interactive portfolio dashboard.
- Interview-ready case study PowerPoint deck.
- Meridian and Vertex AI positioning note clarifying what is future production path versus current prototype.

Latest project memo:

```text
reports/phase3_route_opportunity_memo.md
reports/phase4_marketing_response_memo.md
reports/phase4b_marketing_sensitivity_memo.md
reports/phase5_budget_optimization_memo.md
reports/phase6_experiment_design_memo.md
reports/final_portfolio_case_study.md
reports/interview_talk_track_cn.md
docs/18_meridian_vertex_positioning.md
presentations/regional_route_marketing_science_case_study.pptx
```

Reviewer starting point:

```text
reports/final_portfolio_case_study.md
dashboard/route_marketing_portfolio_dashboard.html
presentations/regional_route_marketing_science_case_study.pptx
```
