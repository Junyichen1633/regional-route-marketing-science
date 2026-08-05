# Phase 4B Memo: Marketing Sensitivity and Recovery Analysis V0

## Business Question

If marketing data is simulated, under what conditions can a marketing model recover the correct channel ranking and budget direction?

## Why This Matters

The project should not claim that simulated marketing spend proves true MMM performance. Instead, the useful question is whether the modeling workflow is robust under plausible data-generating mechanisms.

## Simulation Design

The sensitivity layer varies two dimensions:

- Marketing spend generation: randomized, demand-following, risk-targeting, seasonal campaign, and bundled-channel spend.
- True effect strength: weak, base, and strong.

Each scenario is run for 40 deterministic replications and evaluated with three model specs:

- `naive_raw_spend`: raw spend without controls.
- `controlled_adstock`: adstocked spend with route and month controls.
- `controlled_saturation`: an MMM-like response transformation with adstock, saturation, route controls, and month controls.

## High-Level Result

- Controlled/saturation average top-channel recovery: 58%.
- Controlled/adstock average top-channel recovery: 54%.
- Naive raw-spend average top-channel recovery: 8%.
- Controlled/saturation average budget-efficiency ratio: 93%.
- Controlled/adstock average budget-efficiency ratio: 90%.
- Naive raw-spend average budget-efficiency ratio: 82%.

## Interpretation

If effects are weak or channels are bought as a tight bundle, channel-level ranking becomes fragile. In those cases, the project should emphasize route-level budget direction, experiment design, and grouped-channel guardrails rather than precise channel rank claims.

The recovery results show that exogenous spend variation alone is not enough in a small, noisy panel. Channel ranking becomes more credible only when true effects are strong enough, channels are not tightly bundled, outcomes are measured cleanly, and the model includes adstock/saturation structure. That supports the project framing: Meridian or any MMM component should be used as a measurement module only when real spend variation and outcomes are strong enough.

## Next Step

Use this sensitivity layer in the portfolio package as the evidence that the project understands simulated marketing limitations and validates model recovery before claiming optimization value.
