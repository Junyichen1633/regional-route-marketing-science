# Phase 4B Marketing Sensitivity and Recovery Analysis

## Objective

Test whether simulated marketing data can support credible channel-ranking and budget-direction claims.

This phase answers:

```text
Under different marketing data-generating mechanisms and true effect strengths, can the model recover the correct channel ordering and budget direction?
```

## Why This Exists

The project does not currently have observed route-level marketing spend.

That means the project should not claim:

- true MMM attribution
- measured channel ROI
- observed causal budget optimization

Instead, the valuable analysis is a recovery test:

- simulate plausible marketing spend mechanisms
- simulate known true channel effects
- fit candidate model specifications
- check whether the model recovers the known truth

## Inputs

Truth assumptions:

```text
config/marketing_channel_truth_assumptions.csv
```

Sensitivity scenarios:

```text
config/marketing_sensitivity_scenarios.csv
```

Existing project inputs:

```text
data/processed/route_month_panel_v2.csv
data/processed/route_opportunity_score_v0.csv
data/processed/marketing_response_route_summary_v0.csv
```

## Outputs

Replicate-level simulation output:

```text
data/processed/marketing_sensitivity_replicates_v0.csv
```

Scenario-level summary:

```text
data/processed/marketing_sensitivity_summary_v0.csv
```

Human-readable outputs:

```text
outputs/marketing_sensitivity_analysis_v0_summary.md
reports/phase4b_marketing_sensitivity_memo.md
```

## Simulated Marketing Mechanisms

The v0 sensitivity layer tests five spend-generation mechanisms:

- `randomized`: spend varies mostly exogenously.
- `demand_following`: spend follows high-demand routes and peak months.
- `risk_targeting`: spend targets weaker routes or soft months.
- `seasonal_campaign`: spend is concentrated in campaign windows.
- `channel_bundle`: channels are bought together, creating high collinearity.

Each mechanism is tested under three true effect strengths:

- `weak`
- `base`
- `strong`

Each scenario is run for 40 deterministic replications.

## Model Specifications

`naive_raw_spend`

Raw channel spend without controls. This is intentionally a weak baseline and shows how misleading naive channel ranking can be.

`controlled_adstock`

Adstocked spend with route and month controls.

`controlled_saturation`

An MMM-like response transformation with adstock, saturation, route controls, and month controls.

## Recovery Metrics

`top_channel_recovery_rate`

Share of replications where the model identifies the true strongest channel.

`mean_top2_budget_direction_overlap`

Average overlap between the model-implied top two channels and the true top two channels.

`mean_budget_efficiency_ratio`

True value of the model-implied channel budget direction divided by the true optimal channel budget direction.

`mean_spearman_rank_corr`

Rank correlation between true and estimated channel ordering.

## Current Readout

Across all simulated mechanisms and effect strengths:

- Controlled/saturation average top-channel recovery: 58%.
- Controlled/adstock average top-channel recovery: 54%.
- Naive raw-spend average top-channel recovery: 8%.
- Controlled/saturation average budget-efficiency ratio: 93%.
- Controlled/adstock average budget-efficiency ratio: 90%.
- Naive raw-spend average budget-efficiency ratio: 82%.

The strongest interpretation is:

```text
Budget direction is more stable than exact channel ranking.
```

The model can often point budget in a useful direction, but precise channel ordering is fragile when effects are weak, channels are bundled, or measurement noise is high.

## Business Implication

For the portfolio narrative, do not claim:

```text
Paid search is definitively the best channel because the simulated MMM says so.
```

Claim instead:

```text
The recovery analysis shows that channel-level rank claims require real spend variation and partner outcome data. Until then, the model should be used for route-level portfolio direction, scenario planning, and experiment prioritization.
```

## Next Step

Use this sensitivity layer in the final portfolio package to show measurement maturity:

- explain what simulated marketing can and cannot prove
- show when MMM-like recovery works
- show when channel ranking becomes fragile
- connect uncertainty to experiment design and budget guardrails
