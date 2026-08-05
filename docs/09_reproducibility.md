# Reproducibility Notes

## Environment

The current Phase 1 scripts use only the Python standard library.

No package installation is required.

The PowerPoint deck builder uses the bundled Codex presentation runtime and `@oai/artifact-tool`; it does not require installing project-level npm packages.

## Script Order

From the project root:

```bash
python3 src/build_route_month_skeleton.py
python3 src/build_statcan_context_tables.py
python3 src/build_statcan_airport_movements.py
python3 src/build_panel_v0.py
python3 src/build_panel_v1.py
python3 src/build_route_supply_monthly.py
python3 src/build_panel_v2.py
python3 src/train_route_active_baseline.py
python3 src/build_route_opportunity_score.py
python3 src/build_marketing_response_scenarios.py
python3 src/run_marketing_sensitivity_analysis.py
python3 src/optimize_budget_allocations.py
python3 src/build_experiment_design.py
python3 src/build_portfolio_artifacts.py
python3 src/build_visual_dashboard.py
/Users/chenjunyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node src/build_case_study_deck.mjs
```

For the deck builder, use the bundled Codex Node runtime because the script relies on the bundled `@oai/artifact-tool` presentation package.

## Downloaded Raw Data

The following Statistics Canada full-table CSV bundles were downloaded into `data/raw/statcan/`:

- `23100253`: Air passenger traffic at Canadian airports, annual
- `23100312`: Screened passenger traffic at the largest airports in Canada, monthly
- `23100302`: Domestic and international itinerant movements by type of operation, monthly
- `23100304`: Domestic and international itinerant movements by geography, monthly; inspected and rejected for MVP airport-specific modeling

The download helper is:

```bash
python3 src/download_statcan_table.py --pid <PID>
```

If the local Python certificate chain fails, this project includes an explicit fallback:

```bash
python3 src/download_statcan_table.py --pid <PID> --allow-insecure-ssl
```

For this iteration, `curl` was used successfully for public StatsCan zip files.

## Generated Processed Files

Processed files are not intended to be committed by default because they can be regenerated.

Key generated files:

- `data/processed/route_month_skeleton.csv`
- `data/processed/statcan_airport_annual_passengers.csv`
- `data/processed/statcan_screened_monthly_passengers.csv`
- `data/processed/statcan_airport_monthly_movements.csv`
- `data/processed/route_month_panel_v0.csv`
- `data/processed/route_month_panel_v1.csv`
- `data/processed/route_supply_monthly_v0.csv`
- `data/processed/route_month_panel_v2.csv`
- `data/processed/route_opportunity_score_v0.csv`
- `data/processed/marketing_response_curve_v0.csv`
- `data/processed/marketing_response_route_summary_v0.csv`
- `data/processed/marketing_sensitivity_replicates_v0.csv`
- `data/processed/marketing_sensitivity_summary_v0.csv`
- `data/processed/budget_optimization_case_summary_v0.csv`
- `data/processed/budget_optimization_allocations_v0.csv`
- `data/processed/experiment_design_plan_v0.csv`
- `data/processed/experiment_control_matches_v0.csv`

## Generated Output Summaries

Output summaries are written to `outputs/` and can be regenerated from scripts.

Key summaries:

- `outputs/route_month_skeleton_summary.md`
- `outputs/statcan_airport_traffic_coverage.md`
- `outputs/statcan_context_tables_summary.md`
- `outputs/statcan_airport_movements_summary.md`
- `outputs/route_month_panel_v0_summary.md`
- `outputs/route_month_panel_v1_summary.md`
- `outputs/route_supply_monthly_v0_summary.md`
- `outputs/route_month_panel_v2_summary.md`
- `outputs/route_active_baseline_v0.md`
- `outputs/route_active_baseline_metrics.json`
- `outputs/route_opportunity_score_v0_summary.md`
- `outputs/marketing_response_scenarios_v0_summary.md`
- `outputs/marketing_sensitivity_analysis_v0_summary.md`
- `outputs/budget_optimization_v0_summary.md`
- `outputs/experiment_design_v0_summary.md`
- `outputs/final_portfolio_snapshot.md`
- `outputs/visual_dashboard_summary.md`
- `outputs/opensky_probe_CYKF_departure_2024-07-15.md`

Key generated reports:

- `reports/phase1_data_feasibility_memo.md`
- `reports/phase2_route_supply_memo.md`
- `reports/phase3_route_opportunity_memo.md`
- `reports/phase4_marketing_response_memo.md`
- `reports/phase4b_marketing_sensitivity_memo.md`
- `reports/phase5_budget_optimization_memo.md`
- `reports/phase6_experiment_design_memo.md`
- `reports/final_portfolio_case_study.md`
- `reports/interview_talk_track_cn.md`

Key generated dashboards:

- `dashboard/route_marketing_portfolio_dashboard.html`

Key generated presentations:

- `presentations/regional_route_marketing_science_case_study.pptx`
