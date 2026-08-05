"""Build a standalone visual dashboard for the route marketing portfolio."""

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

ROUTE_SCORE_FILE = PROCESSED_DIR / "route_opportunity_score_v0.csv"
BUDGET_CASE_FILE = PROCESSED_DIR / "budget_optimization_case_summary_v0.csv"
BUDGET_ALLOCATION_FILE = PROCESSED_DIR / "budget_optimization_allocations_v0.csv"
SENSITIVITY_FILE = PROCESSED_DIR / "marketing_sensitivity_summary_v0.csv"
EXPERIMENT_FILE = PROCESSED_DIR / "experiment_design_plan_v0.csv"
CONTROL_MATCH_FILE = PROCESSED_DIR / "experiment_control_matches_v0.csv"

DASHBOARD_FILE = DASHBOARD_DIR / "route_marketing_portfolio_dashboard.html"
SUMMARY_FILE = OUTPUTS_DIR / "visual_dashboard_summary.md"


AIRPORT_COORDS = {
    "YKF": {"name": "Waterloo Region", "lat": 43.46, "lon": -80.38},
    "YHM": {"name": "Hamilton", "lat": 43.17, "lon": -79.93},
    "YXU": {"name": "London", "lat": 43.03, "lon": -81.15},
    "YXX": {"name": "Abbotsford", "lat": 49.03, "lon": -122.36},
    "YLW": {"name": "Kelowna", "lat": 49.96, "lon": -119.38},
    "YVR": {"name": "Vancouver", "lat": 49.19, "lon": -123.18},
    "YYC": {"name": "Calgary", "lat": 51.12, "lon": -114.01},
    "YEG": {"name": "Edmonton", "lat": 53.31, "lon": -113.58},
    "YHZ": {"name": "Halifax", "lat": 44.88, "lon": -63.51},
    "YYZ": {"name": "Toronto", "lat": 43.68, "lon": -79.63},
}


NUMERIC_FIELDS = {
    "total_budget_cad",
    "allocated_budget_cad",
    "unspent_budget_cad",
    "funded_routes",
    "active_routes_funded",
    "relaunch_routes_funded",
    "relaunch_budget_cad",
    "incremental_passenger_proxy",
    "incremental_route_health_points",
    "cost_per_incremental_passenger_proxy_cad",
    "objective_value",
    "campaign_budget_cad",
    "capacity_required_flag",
    "marketing_support_priority_score_v0",
    "route_sustainability_score_v0",
    "data_confidence_score",
    "distance_km",
    "label_coverage_2023_2025",
    "active_rate_2023_2025",
    "recent_active_rate_2025",
    "median_weekly_frequency_proxy_2023_2025",
    "competition_pressure_score",
    "demand_context_score",
    "service_viability_score",
    "regional_strategic_fit_score",
    "service_gap_score",
    "opportunity_rank_target_only",
    "effect_multiplier",
    "noise_pct",
    "replications",
    "top_channel_recovery_rate",
    "mean_top2_budget_direction_overlap",
    "mean_spearman_rank_corr",
    "mean_budget_efficiency_ratio",
    "mean_positive_sign_accuracy",
    "pre_period_weeks",
    "test_period_weeks",
    "post_period_weeks",
    "baseline_annual_passenger_proxy",
    "expected_incremental_passenger_proxy",
    "expected_incremental_pct_of_baseline_proxy",
    "planned_mde_pct",
    "match_rank",
    "match_score",
}


def read_csv(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows: list[dict[str, object]] = []
        for row in csv.DictReader(handle):
            converted: dict[str, object] = {}
            for key, value in row.items():
                if key in NUMERIC_FIELDS and value != "":
                    converted[key] = float(value)
                else:
                    converted[key] = value
            rows.append(converted)
        return rows


def build_payload() -> dict[str, object]:
    cases = read_csv(BUDGET_CASE_FILE)
    allocations = read_csv(BUDGET_ALLOCATION_FILE)
    routes = read_csv(ROUTE_SCORE_FILE)
    sensitivity = read_csv(SENSITIVITY_FILE)
    experiments = read_csv(EXPERIMENT_FILE)
    controls = read_csv(CONTROL_MATCH_FILE)

    recommended_case = next(case for case in cases if case["case_id"] == "portfolio_value_500k")
    recommended_allocations = [
        allocation for allocation in allocations if allocation["case_id"] == "portfolio_value_500k"
    ]

    sensitivity_average: dict[str, dict[str, float]] = {}
    for model_spec in sorted({str(row["model_spec"]) for row in sensitivity}):
        rows = [row for row in sensitivity if row["model_spec"] == model_spec]
        sensitivity_average[model_spec] = {
            "top_channel_recovery_rate": sum(float(row["top_channel_recovery_rate"]) for row in rows)
            / len(rows),
            "mean_top2_budget_direction_overlap": sum(
                float(row["mean_top2_budget_direction_overlap"]) for row in rows
            )
            / len(rows),
            "mean_budget_efficiency_ratio": sum(float(row["mean_budget_efficiency_ratio"]) for row in rows)
            / len(rows),
            "mean_spearman_rank_corr": sum(float(row["mean_spearman_rank_corr"]) for row in rows)
            / len(rows),
        }

    return {
        "cases": cases,
        "allocations": allocations,
        "routes": routes,
        "sensitivity": sensitivity,
        "sensitivityAverage": sensitivity_average,
        "experiments": experiments,
        "controls": controls,
        "airportCoords": AIRPORT_COORDS,
        "recommendedCase": recommended_case,
        "recommendedAllocations": recommended_allocations,
    }


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Regional Air Route Marketing Science Dashboard</title>
  <style>
    :root {
      --paper: #f6f8f5;
      --surface: #ffffff;
      --surface-alt: #eef3f1;
      --ink: #23262b;
      --muted: #66706d;
      --line: #d8dedb;
      --green: #23756b;
      --blue: #2f6ea5;
      --amber: #c47c2c;
      --red: #b84a45;
      --violet: #755e9a;
      --shadow: 0 14px 30px rgba(29, 39, 44, 0.09);
      --radius: 8px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      min-width: 320px;
    }

    button, select {
      font: inherit;
    }

    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
    }

    .sidebar {
      background: #20272a;
      color: #f7faf8;
      padding: 24px 20px;
      border-right: 1px solid rgba(255, 255, 255, 0.08);
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
    }

    .brand {
      display: grid;
      gap: 8px;
      margin-bottom: 28px;
    }

    .brand-mark {
      width: 40px;
      height: 40px;
      border-radius: var(--radius);
      background: linear-gradient(135deg, var(--green), var(--amber));
      display: grid;
      place-items: center;
      font-weight: 800;
      color: white;
    }

    .brand h1 {
      font-size: 18px;
      line-height: 1.18;
      margin: 0;
      font-weight: 750;
    }

    .brand p {
      color: #b7c2be;
      margin: 0;
      font-size: 13px;
      line-height: 1.45;
    }

    .nav {
      display: grid;
      gap: 8px;
    }

    .nav button {
      border: 0;
      width: 100%;
      text-align: left;
      padding: 10px 12px;
      color: #d8e2de;
      background: transparent;
      border-left: 3px solid transparent;
      cursor: pointer;
    }

    .nav button.active {
      background: rgba(255, 255, 255, 0.08);
      border-left-color: var(--amber);
      color: white;
    }

    .sidebar-note {
      margin-top: 28px;
      padding: 12px;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: var(--radius);
      color: #dbe5e1;
      font-size: 12px;
      line-height: 1.5;
    }

    main {
      min-width: 0;
    }

    .topbar {
      background: rgba(246, 248, 245, 0.92);
      border-bottom: 1px solid var(--line);
      padding: 18px 28px;
      position: sticky;
      top: 0;
      z-index: 8;
      backdrop-filter: blur(12px);
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: center;
    }

    .topbar h2 {
      margin: 0;
      font-size: 20px;
    }

    .topbar p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .case-select {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .case-select label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }

    select {
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--ink);
      padding: 8px 30px 8px 10px;
      border-radius: var(--radius);
      min-width: 240px;
    }

    .content {
      padding: 24px 28px 36px;
      display: grid;
      gap: 22px;
    }

    .view {
      display: none;
      gap: 22px;
    }

    .view.active {
      display: grid;
    }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      gap: 12px;
    }

    .kpi {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 14px;
      box-shadow: var(--shadow);
      min-height: 96px;
    }

    .kpi .label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .kpi .value {
      font-size: 26px;
      font-weight: 760;
      margin-top: 8px;
      white-space: nowrap;
    }

    .kpi .hint {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }

    .grid-two {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
      gap: 16px;
    }

    .grid-three {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }

    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .panel-head {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }

    .panel-head h3 {
      margin: 0;
      font-size: 15px;
    }

    .panel-head span {
      color: var(--muted);
      font-size: 12px;
    }

    .panel-body {
      padding: 16px;
    }

    .map-wrap {
      position: relative;
      min-height: 420px;
    }

    #routeMap {
      width: 100%;
      height: 420px;
      display: block;
      background: #edf2ef;
      border-radius: var(--radius);
      border: 1px solid var(--line);
    }

    .legend {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 12px;
      color: var(--muted);
      font-size: 12px;
    }

    .legend span {
      display: inline-flex;
      gap: 6px;
      align-items: center;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--green);
      display: inline-block;
    }

    .dot.relaunch { background: var(--amber); }
    .dot.maintain { background: var(--blue); }
    .dot.evidence { background: var(--violet); }

    .route-list {
      display: grid;
      gap: 8px;
      max-height: 414px;
      overflow: auto;
      padding-right: 4px;
    }

    .route-row {
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: var(--radius);
      padding: 10px 12px;
      cursor: pointer;
      display: grid;
      grid-template-columns: 88px minmax(0, 1fr) 90px;
      gap: 10px;
      align-items: center;
      min-height: 60px;
    }

    .route-row.active {
      border-color: var(--green);
      box-shadow: inset 3px 0 0 var(--green);
    }

    .route-code {
      font-weight: 760;
      white-space: nowrap;
    }

    .route-meta {
      color: var(--muted);
      font-size: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .route-budget {
      text-align: right;
      font-weight: 720;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: var(--surface-alt);
      color: var(--ink);
      border: 1px solid var(--line);
      white-space: nowrap;
    }

    .pill.relaunch_feasibility { border-color: rgba(196, 124, 44, 0.45); color: #825018; background: #fbf1e4; }
    .pill.scale_defend { border-color: rgba(35, 117, 107, 0.45); color: #15564e; background: #e5f2ef; }
    .pill.test_and_learn { border-color: rgba(47, 110, 165, 0.42); color: #244f77; background: #e8f0f8; }
    .pill.maintain { border-color: rgba(117, 94, 154, 0.34); color: #53416f; background: #f1edf7; }

    .detail-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .metric {
      background: var(--surface-alt);
      border-radius: var(--radius);
      padding: 10px;
      min-height: 70px;
    }

    .metric strong {
      display: block;
      font-size: 20px;
      margin-bottom: 4px;
    }

    .metric span {
      color: var(--muted);
      font-size: 12px;
    }

    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 12px;
    }

    .section-title h3 {
      margin: 0;
      font-size: 16px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    th, td {
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }

    th {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0;
      background: #f8faf8;
      position: sticky;
      top: 0;
    }

    td.num, th.num {
      text-align: right;
      white-space: nowrap;
    }

    .bar-list {
      display: grid;
      gap: 10px;
    }

    .bar-row {
      display: grid;
      grid-template-columns: 168px minmax(100px, 1fr) 64px;
      align-items: center;
      gap: 10px;
      font-size: 13px;
    }

    .bar-track {
      height: 12px;
      background: var(--surface-alt);
      border-radius: 999px;
      overflow: hidden;
      border: 1px solid var(--line);
    }

    .bar-fill {
      height: 100%;
      background: var(--green);
      width: 0%;
    }

    .bar-fill.blue { background: var(--blue); }
    .bar-fill.amber { background: var(--amber); }
    .bar-fill.red { background: var(--red); }

    .scenario-table-wrap,
    .experiment-table-wrap {
      overflow: auto;
      max-height: 430px;
    }

    .callout {
      border-left: 4px solid var(--amber);
      background: #fff8ee;
      padding: 12px 14px;
      border-radius: var(--radius);
      color: #624015;
      line-height: 1.5;
      font-size: 13px;
    }

    .empty {
      color: var(--muted);
      font-size: 13px;
    }

    @media (max-width: 1050px) {
      .shell {
        grid-template-columns: 1fr;
      }
      .sidebar {
        position: static;
        height: auto;
      }
      .nav {
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }
      .topbar {
        position: static;
        flex-direction: column;
        align-items: stretch;
      }
      .case-select {
        justify-content: flex-start;
      }
      .kpi-grid,
      .grid-three,
      .grid-two {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 640px) {
      .content,
      .topbar {
        padding-left: 16px;
        padding-right: 16px;
      }
      .nav {
        grid-template-columns: 1fr 1fr;
      }
      .kpi-grid {
        grid-template-columns: 1fr 1fr;
      }
      .route-row {
        grid-template-columns: 74px minmax(0, 1fr);
      }
      .route-budget {
        grid-column: 1 / -1;
        text-align: left;
      }
      .bar-row {
        grid-template-columns: 1fr;
        gap: 5px;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">RM</div>
        <h1>Regional Route Marketing Science</h1>
        <p>Portfolio view for route opportunity, response sensitivity, budget allocation, and validation design.</p>
      </div>
      <nav class="nav" aria-label="Dashboard sections">
        <button class="active" type="button" data-view="portfolio">Portfolio</button>
        <button type="button" data-view="sensitivity">Sensitivity</button>
        <button type="button" data-view="experiments">Experiments</button>
        <button type="button" data-view="method">Method</button>
      </nav>
      <div class="sidebar-note">
        Passenger and lift values are proxies. The dashboard supports planning and experiment prioritization, not observed causal channel ROI.
      </div>
    </aside>

    <main>
      <header class="topbar">
        <div>
          <h2 id="viewTitle">Portfolio Allocation</h2>
          <p id="viewSubtitle">Recommended budget plan, route map, and allocation details.</p>
        </div>
        <div class="case-select">
          <label for="caseSelect">Optimization case</label>
          <select id="caseSelect"></select>
        </div>
      </header>

      <section class="content">
        <div id="portfolio" class="view active">
          <div class="kpi-grid" id="kpiGrid"></div>

          <div class="grid-two">
            <section class="panel">
              <div class="panel-head">
                <h3>Route Portfolio Map</h3>
                <span id="mapHint">Funded route network</span>
              </div>
              <div class="panel-body">
                <div class="map-wrap">
                  <canvas id="routeMap" width="980" height="520"></canvas>
                </div>
                <div class="legend">
                  <span><i class="dot"></i>Scale / test</span>
                  <span><i class="dot relaunch"></i>Relaunch feasibility</span>
                  <span><i class="dot maintain"></i>Maintain</span>
                  <span><i class="dot evidence"></i>Evidence first</span>
                </div>
              </div>
            </section>

            <section class="panel">
              <div class="panel-head">
                <h3>Funded Routes</h3>
                <span id="routeCount"></span>
              </div>
              <div class="panel-body">
                <div class="route-list" id="routeList"></div>
              </div>
            </section>
          </div>

          <div class="grid-two">
            <section class="panel">
              <div class="panel-head">
                <h3 id="selectedRouteTitle">Route Detail</h3>
                <span id="selectedRouteStatus"></span>
              </div>
              <div class="panel-body">
                <div class="detail-grid" id="routeDetails"></div>
              </div>
            </section>

            <section class="panel">
              <div class="panel-head">
                <h3>Case Comparison</h3>
                <span>Objective tradeoffs</span>
              </div>
              <div class="panel-body scenario-table-wrap">
                <table id="caseTable"></table>
              </div>
            </section>
          </div>
        </div>

        <div id="sensitivity" class="view">
          <div class="grid-three">
            <section class="panel">
              <div class="panel-head"><h3>Recovery Summary</h3><span>Average across scenarios</span></div>
              <div class="panel-body"><div id="sensitivityBars" class="bar-list"></div></div>
            </section>
            <section class="panel">
              <div class="panel-head"><h3>Mechanism Stress Test</h3><span>Controlled saturation</span></div>
              <div class="panel-body"><div id="mechanismBars" class="bar-list"></div></div>
            </section>
            <section class="panel">
              <div class="panel-head"><h3>Interpretation</h3><span>Planning caveat</span></div>
              <div class="panel-body">
                <div class="callout">
                  Budget direction is more stable than exact channel ranking. Simulated spend can guide scenario planning, but precise channel ROI still needs real spend variation and partner outcome data.
                </div>
              </div>
            </section>
          </div>
          <section class="panel">
            <div class="panel-head"><h3>Sensitivity Scenario Table</h3><span>Model recovery by mechanism and effect strength</span></div>
            <div class="panel-body scenario-table-wrap">
              <table id="sensitivityTable"></table>
            </div>
          </section>
        </div>

        <div id="experiments" class="view">
          <section class="panel">
            <div class="panel-head"><h3>Validation Plan</h3><span>Recommended case: portfolio_value_500k</span></div>
            <div class="panel-body experiment-table-wrap">
              <table id="experimentTable"></table>
            </div>
          </section>
          <section class="panel">
            <div class="panel-head"><h3>Control Matches</h3><span>Three candidates per funded route</span></div>
            <div class="panel-body experiment-table-wrap">
              <table id="controlTable"></table>
            </div>
          </section>
        </div>

        <div id="method" class="view">
          <div class="grid-two">
            <section class="panel">
              <div class="panel-head"><h3>Model Flow</h3><span>Decision workflow</span></div>
              <div class="panel-body">
                <table>
                  <tbody>
                    <tr><th>1</th><td>Build route-month panel from public airport context and sourced route events.</td></tr>
                    <tr><th>2</th><td>Score route opportunity using service viability, demand context, strategic fit, hub pressure, and evidence confidence.</td></tr>
                    <tr><th>3</th><td>Simulate marketing response curves with adstock and saturation assumptions.</td></tr>
                    <tr><th>4</th><td>Run sensitivity and recovery analysis to test channel ranking and budget direction.</td></tr>
                    <tr><th>5</th><td>Optimize route-budget pairs under portfolio constraints.</td></tr>
                    <tr><th>6</th><td>Validate recommendations with matched-route, geo-lift, or capacity-gated tests.</td></tr>
                  </tbody>
                </table>
              </div>
            </section>
            <section class="panel">
              <div class="panel-head"><h3>Claims And Guardrails</h3><span>Decision-safe framing</span></div>
              <div class="panel-body">
                <div class="callout">
                  The project supports route-level portfolio direction and experiment prioritization under public-data constraints. It does not claim observed causal channel ROI.
                </div>
                <div style="height:12px"></div>
                <table>
                  <tbody>
                    <tr><th>Future production path</th><td>BigQuery for route-month data, Vertex AI Pipelines for reproducible scoring, Meridian when real marketing spend and outcomes exist.</td></tr>
                    <tr><th>Primary missing data</th><td>Route-level bookings, campaign spend, conversion events, load factor, and fare/yield guardrails.</td></tr>
                    <tr><th>Planning point</th><td>Budget direction is more stable than exact channel ranking, so the recommendation must flow into experiments before scaling.</td></tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const DATA = __DATA__;

    const state = {
      view: 'portfolio',
      caseId: 'portfolio_value_500k',
      selectedRoute: null
    };

    const titles = {
      portfolio: ['Portfolio Allocation', 'Recommended budget plan, route map, and allocation details.'],
      sensitivity: ['Marketing Sensitivity', 'Recovery analysis for simulated channel effects and spend mechanisms.'],
      experiments: ['Experiment Design', 'Treatment, comparison routes, success metrics, and validation readiness.'],
      method: ['Method And Guardrails', 'Model flow, production path, and decision-safe claims.']
    };

    const bucketColor = {
      relaunch_feasibility: '#c47c2c',
      scale_defend: '#23756b',
      test_and_learn: '#2f6ea5',
      maintain: '#755e9a',
      evidence_first: '#755e9a',
      low_priority: '#b84a45'
    };

    function fmtMoney(value) {
      return 'CAD ' + Number(value || 0).toLocaleString('en-CA', { maximumFractionDigits: 0 });
    }

    function fmtNum(value, digits = 0) {
      return Number(value || 0).toLocaleString('en-CA', { maximumFractionDigits: digits, minimumFractionDigits: digits });
    }

    function fmtPct(value, digits = 0) {
      return (Number(value || 0) * 100).toFixed(digits) + '%';
    }

    function caseRows() {
      return DATA.allocations.filter(row => row.case_id === state.caseId);
    }

    function caseSummary() {
      return DATA.cases.find(row => row.case_id === state.caseId) || DATA.recommendedCase;
    }

    function routeScore(routeId) {
      return DATA.routes.find(row => row.route_id === routeId) || {};
    }

    function experimentFor(routeId) {
      return DATA.experiments.find(row => row.route_id === routeId) || {};
    }

    function initCaseSelect() {
      const select = document.getElementById('caseSelect');
      select.innerHTML = DATA.cases.map(row => `<option value="${row.case_id}">${row.case_id}</option>`).join('');
      select.value = state.caseId;
      select.addEventListener('change', event => {
        state.caseId = event.target.value;
        state.selectedRoute = null;
        renderPortfolio();
      });
    }

    function initNav() {
      document.querySelectorAll('.nav button').forEach(button => {
        button.addEventListener('click', () => {
          state.view = button.dataset.view;
          document.querySelectorAll('.nav button').forEach(item => item.classList.toggle('active', item === button));
          document.querySelectorAll('.view').forEach(view => view.classList.toggle('active', view.id === state.view));
          document.getElementById('viewTitle').textContent = titles[state.view][0];
          document.getElementById('viewSubtitle').textContent = titles[state.view][1];
          if (state.view === 'portfolio') drawMap();
        });
      });
    }

    function renderKpis() {
      const summary = caseSummary();
      const sensitivity = DATA.sensitivityAverage.controlled_saturation;
      const kpis = [
        ['Allocated Budget', fmtMoney(summary.allocated_budget_cad), summary.case_id],
        ['Funded Routes', fmtNum(summary.funded_routes), `${fmtNum(summary.active_routes_funded)} active / ${fmtNum(summary.relaunch_routes_funded)} relaunch`],
        ['Passenger Proxy', fmtNum(summary.incremental_passenger_proxy), `${fmtMoney(summary.cost_per_incremental_passenger_proxy_cad)} per proxy passenger`],
        ['Route Health Lift', fmtNum(summary.incremental_route_health_points, 1), 'points across funded routes'],
        ['Sensitivity Efficiency', fmtPct(sensitivity.mean_budget_efficiency_ratio), 'controlled saturation average']
      ];
      document.getElementById('kpiGrid').innerHTML = kpis.map(kpi => `
        <article class="kpi">
          <div class="label">${kpi[0]}</div>
          <div class="value">${kpi[1]}</div>
          <div class="hint">${kpi[2]}</div>
        </article>
      `).join('');
    }

    function renderRoutes() {
      const rows = caseRows().sort((a, b) => Number(b.campaign_budget_cad) - Number(a.campaign_budget_cad) || a.route_id.localeCompare(b.route_id));
      if (!state.selectedRoute && rows.length) state.selectedRoute = rows[0].route_id;
      document.getElementById('routeCount').textContent = `${rows.length} routes`;
      document.getElementById('routeList').innerHTML = rows.map(row => {
        const active = row.route_id === state.selectedRoute ? 'active' : '';
        return `
          <button class="route-row ${active}" type="button" data-route="${row.route_id}">
            <div>
              <div class="route-code">${row.route_id}</div>
              <div class="route-meta">${routeScore(row.route_id).route_segment || row.route_segment}</div>
            </div>
            <div>
              <span class="pill ${row.decision_bucket}">${row.decision_bucket.replaceAll('_', ' ')}</span>
              <div class="route-meta">${row.source_recommendation}</div>
            </div>
            <div class="route-budget">${fmtMoney(row.campaign_budget_cad)}</div>
          </button>
        `;
      }).join('');
      document.querySelectorAll('.route-row').forEach(row => {
        row.addEventListener('click', () => {
          state.selectedRoute = row.dataset.route;
          renderPortfolio();
        });
      });
    }

    function renderRouteDetails() {
      const allocation = caseRows().find(row => row.route_id === state.selectedRoute) || caseRows()[0];
      if (!allocation) {
        document.getElementById('routeDetails').innerHTML = '<p class="empty">No route selected.</p>';
        return;
      }
      const route = routeScore(allocation.route_id);
      const experiment = experimentFor(allocation.route_id);
      document.getElementById('selectedRouteTitle').textContent = allocation.route_id;
      document.getElementById('selectedRouteStatus').textContent = route.recommendation || allocation.source_recommendation;
      const details = [
        [fmtMoney(allocation.campaign_budget_cad), 'Campaign budget'],
        [fmtNum(allocation.incremental_passenger_proxy), 'Incremental passenger proxy'],
        [fmtNum(allocation.incremental_route_health_points, 1), 'Route-health lift points'],
        [fmtNum(route.marketing_support_priority_score_v0, 1), 'Marketing priority score'],
        [fmtNum(route.route_sustainability_score_v0, 1), 'Sustainability score'],
        [experiment.experiment_design || 'n/a', 'Validation design']
      ];
      document.getElementById('routeDetails').innerHTML = details.map(item => `
        <div class="metric"><strong>${item[0]}</strong><span>${item[1]}</span></div>
      `).join('');
    }

    function renderCaseTable() {
      const rows = DATA.cases;
      document.getElementById('caseTable').innerHTML = `
        <thead><tr>
          <th>Case</th><th>Objective</th><th class="num">Budget</th><th class="num">Routes</th><th class="num">Passenger proxy</th><th class="num">Health lift</th>
        </tr></thead>
        <tbody>
          ${rows.map(row => `
            <tr>
              <td>${row.case_id}</td>
              <td>${row.objective}</td>
              <td class="num">${fmtMoney(row.allocated_budget_cad)}</td>
              <td class="num">${fmtNum(row.funded_routes)}</td>
              <td class="num">${fmtNum(row.incremental_passenger_proxy)}</td>
              <td class="num">${fmtNum(row.incremental_route_health_points, 1)}</td>
            </tr>
          `).join('')}
        </tbody>
      `;
    }

    function lonLatToXY(coord, canvas) {
      const bounds = { minLon: -126, maxLon: -62, minLat: 41, maxLat: 55 };
      const pad = 36;
      const x = pad + ((coord.lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * (canvas.width - pad * 2);
      const y = canvas.height - pad - ((coord.lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * (canvas.height - pad * 2);
      return { x, y };
    }

    function drawMap() {
      const canvas = document.getElementById('routeMap');
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(420 * dpr);
      ctx.scale(dpr, dpr);
      const width = rect.width;
      const height = 420;

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#edf2ef';
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = '#d4ddd9';
      ctx.lineWidth = 1;
      for (let i = 0; i < 5; i++) {
        const y = 42 + i * 75;
        ctx.beginPath();
        ctx.moveTo(30, y);
        ctx.lineTo(width - 30, y);
        ctx.stroke();
      }

      const rows = caseRows();
      const selected = state.selectedRoute;
      rows.forEach(row => {
        const [origin, dest] = row.route_id.split('_');
        const a = lonLatToXY(DATA.airportCoords[origin], { width, height });
        const b = lonLatToXY(DATA.airportCoords[dest], { width, height });
        const midX = (a.x + b.x) / 2;
        const midY = Math.min(a.y, b.y) - Math.max(24, Math.abs(a.x - b.x) * 0.12);
        const isSelected = row.route_id === selected;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.quadraticCurveTo(midX, midY, b.x, b.y);
        ctx.strokeStyle = bucketColor[row.decision_bucket] || '#23756b';
        ctx.globalAlpha = isSelected ? 0.95 : 0.34;
        ctx.lineWidth = isSelected ? 4 : 2;
        ctx.stroke();
        ctx.globalAlpha = 1;
      });

      const airportCodes = new Set();
      rows.forEach(row => {
        const [origin, dest] = row.route_id.split('_');
        airportCodes.add(origin);
        airportCodes.add(dest);
      });
      airportCodes.forEach(code => {
        const point = lonLatToXY(DATA.airportCoords[code], { width, height });
        const isSelected = selected && selected.split('_').includes(code);
        ctx.beginPath();
        ctx.arc(point.x, point.y, isSelected ? 6 : 4, 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? '#20272a' : '#596663';
        ctx.fill();
        ctx.font = '12px Inter, system-ui, sans-serif';
        ctx.fillStyle = '#2b3033';
        ctx.fillText(code, point.x + 8, point.y - 8);
      });

      ctx.fillStyle = '#66706d';
      ctx.font = '12px Inter, system-ui, sans-serif';
      ctx.fillText('Schematic route map, not geographic scale-perfect', 16, height - 16);
    }

    function renderSensitivity() {
      const avgRows = [
        ['controlled_saturation', DATA.sensitivityAverage.controlled_saturation],
        ['controlled_adstock', DATA.sensitivityAverage.controlled_adstock],
        ['naive_raw_spend', DATA.sensitivityAverage.naive_raw_spend]
      ];
      document.getElementById('sensitivityBars').innerHTML = avgRows.map(([name, row], index) => {
        const cls = index === 0 ? '' : index === 1 ? 'blue' : 'red';
        return `
          <div class="bar-row">
            <div>${name}</div>
            <div class="bar-track"><div class="bar-fill ${cls}" style="width:${Math.round(row.mean_budget_efficiency_ratio * 100)}%"></div></div>
            <div>${fmtPct(row.mean_budget_efficiency_ratio)}</div>
          </div>
        `;
      }).join('');

      const mechanismRows = DATA.sensitivity
        .filter(row => row.model_spec === 'controlled_saturation')
        .reduce((acc, row) => {
          acc[row.spend_mechanism] = acc[row.spend_mechanism] || { n: 0, top: 0, efficiency: 0 };
          acc[row.spend_mechanism].n += 1;
          acc[row.spend_mechanism].top += Number(row.top_channel_recovery_rate);
          acc[row.spend_mechanism].efficiency += Number(row.mean_budget_efficiency_ratio);
          return acc;
        }, {});
      document.getElementById('mechanismBars').innerHTML = Object.entries(mechanismRows).map(([name, row]) => {
        const value = row.top / row.n;
        return `
          <div class="bar-row">
            <div>${name}</div>
            <div class="bar-track"><div class="bar-fill amber" style="width:${Math.round(value * 100)}%"></div></div>
            <div>${fmtPct(value)}</div>
          </div>
        `;
      }).join('');

      document.getElementById('sensitivityTable').innerHTML = `
        <thead><tr>
          <th>Mechanism</th><th>Effect</th><th>Model</th><th class="num">Top recovery</th><th class="num">Top-2 overlap</th><th class="num">Budget efficiency</th>
        </tr></thead>
        <tbody>
          ${DATA.sensitivity.map(row => `
            <tr>
              <td>${row.spend_mechanism}</td>
              <td>${row.effect_strength}</td>
              <td>${row.model_spec}</td>
              <td class="num">${fmtPct(row.top_channel_recovery_rate)}</td>
              <td class="num">${fmtPct(row.mean_top2_budget_direction_overlap)}</td>
              <td class="num">${fmtPct(row.mean_budget_efficiency_ratio)}</td>
            </tr>
          `).join('')}
        </tbody>
      `;
    }

    function renderExperiments() {
      document.getElementById('experimentTable').innerHTML = `
        <thead><tr>
          <th>Route</th><th>Budget</th><th>Design</th><th>Primary metric</th><th>Comparisons</th><th>MDE</th><th>Power</th>
        </tr></thead>
        <tbody>
          ${DATA.experiments.map(row => {
            const controls = [row.comparison_route_1, row.comparison_route_2, row.comparison_route_3].filter(Boolean).join(', ');
            return `
              <tr>
                <td>${row.route_id}</td>
                <td class="num">${fmtMoney(row.campaign_budget_cad)}</td>
                <td>${row.experiment_design}</td>
                <td>${row.primary_metric}</td>
                <td>${controls}</td>
                <td class="num">${fmtPct(row.planned_mde_pct, 1)}</td>
                <td>${row.power_readiness}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      `;

      document.getElementById('controlTable').innerHTML = `
        <thead><tr>
          <th>Treatment</th><th>Control</th><th class="num">Rank</th><th class="num">Match score</th><th>Notes</th>
        </tr></thead>
        <tbody>
          ${DATA.controls.map(row => `
            <tr>
              <td>${row.treatment_route_id}</td>
              <td>${row.control_route_id}</td>
              <td class="num">${fmtNum(row.match_rank)}</td>
              <td class="num">${fmtNum(row.match_score, 1)}</td>
              <td>${row.match_notes}</td>
            </tr>
          `).join('')}
        </tbody>
      `;
    }

    function renderPortfolio() {
      renderKpis();
      renderRoutes();
      renderRouteDetails();
      renderCaseTable();
      drawMap();
    }

    function renderAll() {
      initCaseSelect();
      initNav();
      renderPortfolio();
      renderSensitivity();
      renderExperiments();
      window.addEventListener('resize', () => {
        if (state.view === 'portfolio') drawMap();
      });
    }

    renderAll();
  </script>
</body>
</html>
"""


def write_dashboard() -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    DASHBOARD_FILE.write_text(html, encoding="utf-8")

    summary_lines = [
        "# Visual Dashboard Summary",
        "",
        "Generated a standalone dashboard for the route marketing portfolio.",
        "",
        f"- Dashboard file: `{DASHBOARD_FILE.relative_to(PROJECT_ROOT)}`",
        "- Runtime: static HTML, no server required",
        "- Main sections: Portfolio, Sensitivity, Experiments, Method",
        "- Data source: generated CSV outputs from Phases 3-6",
        "",
        "Open the dashboard directly in a browser from the project folder.",
    ]
    SUMMARY_FILE.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> None:
    write_dashboard()
    print(f"Wrote {DASHBOARD_FILE}")
    print(f"Wrote {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
