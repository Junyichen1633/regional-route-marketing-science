# Iteration Log

## 2026-08-05

### Decisions

- Reframed the project from pure MMM to a Marketing Science decision-support system.
- Set the three-layer architecture:
  - Route Demand and Supply Model
  - Marketing Response Model
  - Budget Optimization
- Selected Google Meridian as the preferred MMM component, not the primary model.
- Documented that synthetic marketing spend must be labeled as scenario-based simulation.

### Next

- Validate data availability.
- Choose MVP airport and route set.
- Define the first route-month panel schema.
- Start with EDA before advanced modeling.

## 2026-08-05 Continued

### Completed

- Created MVP airport and seed route configs.
- Generated a 1,296-row route-month skeleton for 18 seed routes across 2020-2025.
- Downloaded Statistics Canada Table 23-10-0253-01 and confirmed it is annual airport-level demand context, not route-month demand.
- Downloaded Statistics Canada Table 23-10-0312-01 and processed monthly screened passenger context for major airports.
- Downloaded Statistics Canada Table 23-10-0302-01 and found complete monthly airport movement coverage for all MVP airports.
- Rejected Statistics Canada Table 23-10-0304-01 for MVP airport modeling because it does not provide specific airport rows.
- Probed OpenSky for CYKF departures and received HTTP 403, so it is blocked without authentication for now.
- Built `route_month_panel_v1` with full airport-month supply/context features.

### Decision

Proceed with a baseline route opportunity and sustainability model, not observed route-month passenger demand. Keep route-level flight frequency as the next data acquisition milestone.

## 2026-08-05 Phase 2

### Completed

- Created `config/route_supply_events.csv` with sourced route-active events.
- Expanded route supply events into `route_supply_monthly_v0`.
- Built `route_month_panel_v2` with route-active labels and direct weekly frequency proxies.
- Achieved 69.0% route-active coverage across 1,296 route-month rows.
- Trained a diagnostic route-active logistic regression baseline.

### Baseline Result

- Temporal split: train on 2020-2024 labeled rows, test on 2025 labeled rows.
- Test ROC AUC: 0.851.

### Caveat

The model is diagnostic only. Labels are sourced from a partial route event table, and the positive class dominates the labeled sample.

### Next

- Improve route-active coverage.
- Build a route opportunity score.
- Start defining marketing response scenarios.

## 2026-08-05 Phase 3

### Completed

- Built `src/build_route_opportunity_score.py`.
- Generated `data/processed/route_opportunity_score_v0.csv`.
- Generated `outputs/route_opportunity_score_v0_summary.md`.
- Generated `reports/phase3_route_opportunity_memo.md`.
- Added end-of-period route status to avoid treating historically active but currently inactive routes as ordinary scale candidates.

### Current Readout

- `YKF_YVR` ranks first as a relaunch feasibility candidate, not as a simple always-on spend target.
- `YKF_YEG`, `YKF_YYC`, `YXX_YYC`, and `YXU_YYC` rank as active-route candidates for controlled marketing tests or defend/scale decisions.
- Hub-to-hub routes remain benchmarks only.
- `YXX_YVR` remains a negative/control route.

### Next

- Build a marketing response scenario module with conservative, base, and optimistic response assumptions.
- Convert response curves into route-level budget allocation recommendations.

## 2026-08-05 Phase 4

### Completed

- Created `config/marketing_response_assumptions.csv`.
- Built `src/build_marketing_response_scenarios.py`.
- Generated `data/processed/marketing_response_curve_v0.csv`.
- Generated `data/processed/marketing_response_route_summary_v0.csv`.
- Generated `outputs/marketing_response_scenarios_v0_summary.md`.
- Generated `reports/phase4_marketing_response_memo.md`.

### Current Readout

- Base-scenario selected test budgets total CAD 875,000 across the 14 target routes.
- Base-scenario incremental passenger proxy total is 25,272.
- Inactive high-priority routes such as `YKF_YVR` and `YXU_YVR` are explicitly marked as capacity-required relaunch scenarios.
- High-volume maintain routes such as `YLW_YVR` need optimizer constraints so they do not dominate purely efficiency-based allocation.

### Next

- Build a constrained budget optimizer using the response curve table.
- Compare objectives: maximize incremental passenger proxy versus maximize route-health lift.

## 2026-08-05 Phase 4B

### Completed

- Created `config/marketing_channel_truth_assumptions.csv`.
- Created `config/marketing_sensitivity_scenarios.csv`.
- Built `src/run_marketing_sensitivity_analysis.py`.
- Generated `data/processed/marketing_sensitivity_replicates_v0.csv`.
- Generated `data/processed/marketing_sensitivity_summary_v0.csv`.
- Generated `outputs/marketing_sensitivity_analysis_v0_summary.md`.
- Generated `reports/phase4b_marketing_sensitivity_memo.md`.

### Current Readout

- Controlled/saturation average top-channel recovery: 58%.
- Controlled/adstock average top-channel recovery: 54%.
- Naive raw-spend average top-channel recovery: 8%.
- Controlled/saturation average budget-efficiency ratio: 93%.
- Controlled/adstock average budget-efficiency ratio: 90%.
- Naive raw-spend average budget-efficiency ratio: 82%.

### Decision

Do not claim precise channel ranking from simulated marketing data. Use the sensitivity result to argue that budget direction and route-level portfolio choices are more stable than exact channel ordering.

### Next

- Carry this caveat into budget optimization and experiment design.
- Use the recovery analysis in the final portfolio package.

## 2026-08-05 Phase 5

### Completed

- Created `config/budget_optimizer_cases.csv`.
- Built `src/optimize_budget_allocations.py`.
- Generated `data/processed/budget_optimization_case_summary_v0.csv`.
- Generated `data/processed/budget_optimization_allocations_v0.csv`.
- Generated `outputs/budget_optimization_v0_summary.md`.
- Generated `reports/phase5_budget_optimization_memo.md`.

### Current Readout

- Recommended planning case: `portfolio_value_500k`.
- Allocated CAD 500,000 across 7 routes.
- Relaunch bucket capped at CAD 75,000.
- Incremental passenger proxy: 16,936.
- Incremental route-health lift: 22.2 points.
- Cost per incremental proxy passenger: CAD 30.

### Recommended Allocation

- `YKF_YEG`: CAD 100,000, scale/defend.
- `YKF_YYC`: CAD 100,000, test-and-learn.
- `YKF_YVR`: CAD 75,000, relaunch feasibility.
- `YXU_YYC`: CAD 75,000, test-and-learn.
- `YXX_YYC`: CAD 75,000, test-and-learn.
- `YXX_YEG`: CAD 50,000, maintain.
- `YLW_YVR`: CAD 25,000, maintain.

### Next

- Build an experiment design layer for the recommended allocation.
- Define treatment/control logic and decision rules.

## 2026-08-05 Phase 6

### Completed

- Created `config/experiment_design_assumptions.csv`.
- Built `src/build_experiment_design.py`.
- Generated `data/processed/experiment_design_plan_v0.csv`.
- Generated `data/processed/experiment_control_matches_v0.csv`.
- Generated `outputs/experiment_design_v0_summary.md`.
- Generated `reports/phase6_experiment_design_memo.md`.

### Current Readout

- Validation plan targets the recommended `portfolio_value_500k` allocation.
- Designed 6 active-route tests and 1 relaunch feasibility test.
- Generated 21 matched control-route candidates.
- `YKF_YVR` is handled as a two-stage capacity-gated relaunch test, not a standard media lift test.

### Next

- Package the project into a polished portfolio artifact.
- Add an executive summary, methodology narrative, model architecture diagram, and final recommendation table.

## 2026-08-05 Phase 7

### Completed

- Built `src/build_portfolio_artifacts.py`.
- Generated `reports/final_portfolio_case_study.md`.
- Generated a Chinese project walkthrough draft.
- Generated `outputs/final_portfolio_snapshot.md`.
- Added a final narrative that frames MMM as one component in a broader route marketing science decision system.

### Current Readout

- Final recommended case remains `portfolio_value_500k`.
- Final portfolio claim is route-level portfolio direction and experiment prioritization, not observed causal channel ROI.
- The sensitivity layer is now part of the main portfolio story.

### Next

- Optionally create a visual dashboard or slide deck from the final artifacts.
- Optionally add a small README quickstart section for reviewers.

## 2026-08-05 Phase 7B

### Completed

- Built `src/build_visual_dashboard.py`.
- Generated `dashboard/route_marketing_portfolio_dashboard.html`.
- Generated `outputs/visual_dashboard_summary.md`.
- Added a standalone dashboard with Portfolio, Sensitivity, Experiments, and Method sections.

### Validation

- Confirmed the HTML file is generated.
- Confirmed embedded JavaScript parses successfully.
- Confirmed the dashboard is standalone and does not require a local server.

### Note

Quick Look previews the static shell but does not execute embedded JavaScript. Open the dashboard directly in a browser for the interactive route map and tables.

## 2026-08-05 Phase 7C

### Completed

- Added `docs/18_meridian_vertex_positioning.md`.
- Built `src/build_case_study_deck.mjs`.
- Generated `presentations/regional_route_marketing_science_case_study.pptx`.
- Added `docs/19_case_study_deck.md`.
- Updated README and reproducibility notes with the deck entry point.

### Current Readout

- The deck frames the project as a route marketing science case study.
- It explicitly says Google Meridian was not run in the current public-data prototype.
- Meridian is positioned as the future MMM component after real route-level spend and outcome data exist.
- Vertex AI is positioned as the future platform path for pipelines, experiment tracking, model comparison, and scheduled scoring.

### Validation

- Exported 8-slide PPTX successfully.
- Rendered slide previews to `work/deck_build/rendered/`.
- Ran `slides_test.py`; no overflow detected.
- Checked the sensitivity chart after fixing the budget-efficiency field mapping.
