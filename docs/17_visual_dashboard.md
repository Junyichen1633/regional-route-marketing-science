# Phase 7B Visual Dashboard

## Objective

Create a standalone portfolio dashboard for reviewing the final route marketing science workflow.

The dashboard is designed for:

- portfolio review
- interview walkthrough
- quick comparison of budget cases
- explaining the sensitivity caveat visually
- connecting route recommendations to experiment design

## Script

```text
src/build_visual_dashboard.py
```

## Output

```text
dashboard/route_marketing_portfolio_dashboard.html
```

The dashboard is a static HTML file. It can be opened directly in a browser and does not require a local server.

## Dashboard Sections

`Portfolio`

- optimization case selector
- KPI summary
- schematic route network map
- funded route list
- selected route detail
- case comparison table

`Sensitivity`

- model recovery comparison
- mechanism-level stress test
- scenario-level recovery table

`Experiments`

- route-level validation plan
- matched comparison routes

`Method`

- model flow
- claims and guardrails
- future Vertex AI / Meridian path

## Design Principle

The dashboard is intentionally quiet and operational. It is not a landing page.

It keeps the first screen focused on the actual decision:

```text
Which route-budget portfolio should be funded, and how should it be validated?
```

## Validation

The generated HTML was checked for:

- embedded data from generated CSV outputs
- JavaScript syntax validity
- standalone file generation
- non-empty dashboard sections
- static consistency against expected output counts:
  - 7 optimization cases
  - 48 allocation rows
  - 18 route opportunity rows
  - 45 sensitivity scenario rows
  - 7 experiment rows
  - 21 matched-control rows

Quick Look can preview the static shell but does not execute the embedded JavaScript. Open the HTML in a browser to see the route map and interactive tables.

Codex in-app browser automation could not open the local `file://` dashboard because of the browser URL policy. This does not affect the dashboard file itself, but it means visual QA inside Codex is limited to the static Quick Look shell plus script/data validation.
