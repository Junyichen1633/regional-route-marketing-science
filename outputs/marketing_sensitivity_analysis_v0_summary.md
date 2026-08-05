# Marketing Sensitivity Analysis V0

This simulation tests whether marketing models recover the correct channel ranking and budget direction under different simulated marketing data-generating mechanisms.

This is stricter than the earlier response scenario analysis: it tests model recovery, not only output sensitivity.

## Key Takeaways

- Controlled/saturation model average budget-efficiency ratio in randomized spend scenarios: 85%.
- Controlled/saturation model average top-2 direction overlap in weak-effect scenarios: 64%.
- Channel-bundle scenarios are the hardest identification setting; controlled/saturation average rank correlation: 0.26.
- Risk-targeting scenarios test negative confounding; controlled/saturation average budget-efficiency ratio: 97%.
- Linear controlled/adstock average top-channel recovery is 54%, which is a useful warning that adstock alone is not enough.

## Controlled / Saturation Model

| Mechanism | Effect | Top channel recovery | Top-2 direction overlap | Rank corr. | Budget efficiency | Dominant estimated top |
|---|---|---:|---:|---:|---:|---|
| channel_bundle | base | 30% | 64% | 0.18 | 87% | paid_social |
| channel_bundle | strong | 40% | 68% | 0.29 | 89% | paid_search |
| channel_bundle | weak | 48% | 68% | 0.31 | 90% | paid_search |
| demand_following | base | 78% | 65% | 0.52 | 96% | paid_search |
| demand_following | strong | 82% | 65% | 0.64 | 97% | paid_search |
| demand_following | weak | 70% | 66% | 0.48 | 95% | paid_search |
| randomized | base | 18% | 51% | 0.11 | 85% | local_ooh |
| randomized | strong | 18% | 56% | 0.21 | 85% | local_ooh |
| randomized | weak | 12% | 46% | 0.07 | 85% | local_ooh |
| risk_targeting | base | 92% | 55% | 0.74 | 98% | paid_search |
| risk_targeting | strong | 92% | 56% | 0.72 | 97% | paid_search |
| risk_targeting | weak | 85% | 55% | 0.65 | 96% | paid_search |
| seasonal_campaign | base | 72% | 75% | 0.66 | 96% | paid_search |
| seasonal_campaign | strong | 72% | 78% | 0.72 | 96% | paid_search |
| seasonal_campaign | weak | 65% | 82% | 0.70 | 96% | paid_search |

## Controlled / Adstock Model

| Mechanism | Effect | Top channel recovery | Top-2 direction overlap | Rank corr. | Budget efficiency | Dominant estimated top |
|---|---|---:|---:|---:|---:|---|
| channel_bundle | base | 25% | 56% | 0.02 | 85% | paid_social |
| channel_bundle | strong | 40% | 68% | 0.24 | 88% | paid_search |
| channel_bundle | weak | 50% | 60% | 0.21 | 89% | paid_search |
| demand_following | base | 100% | 50% | 0.49 | 98% | paid_search |
| demand_following | strong | 98% | 51% | 0.51 | 98% | paid_search |
| demand_following | weak | 95% | 50% | 0.53 | 98% | paid_search |
| randomized | base | 20% | 52% | -0.08 | 82% | display_video |
| randomized | strong | 35% | 57% | 0.14 | 85% | display_video |
| randomized | weak | 22% | 46% | 0.02 | 84% | display_video |
| risk_targeting | base | 25% | 50% | 0.08 | 83% | local_ooh |
| risk_targeting | strong | 12% | 60% | 0.17 | 83% | paid_social |
| risk_targeting | weak | 20% | 61% | 0.26 | 85% | paid_social |
| seasonal_campaign | base | 82% | 52% | 0.47 | 95% | paid_search |
| seasonal_campaign | strong | 92% | 52% | 0.54 | 96% | paid_search |
| seasonal_campaign | weak | 98% | 60% | 0.61 | 97% | paid_search |

## Naive Raw-Spend Model

| Mechanism | Effect | Top channel recovery | Top-2 direction overlap | Rank corr. | Budget efficiency | Dominant estimated top |
|---|---|---:|---:|---:|---:|---|
| channel_bundle | base | 18% | 54% | -0.00 | 84% | paid_social |
| channel_bundle | strong | 25% | 48% | 0.04 | 84% | paid_social |
| channel_bundle | weak | 28% | 46% | 0.10 | 86% | local_ooh |
| demand_following | base | 0% | 50% | -0.20 | 82% | paid_social |
| demand_following | strong | 0% | 50% | -0.20 | 82% | paid_social |
| demand_following | weak | 0% | 50% | -0.20 | 82% | paid_social |
| randomized | base | 15% | 41% | -0.20 | 81% | display_video |
| randomized | strong | 18% | 45% | -0.04 | 83% | local_ooh |
| randomized | weak | 15% | 49% | 0.02 | 84% | local_ooh |
| risk_targeting | base | 0% | 0% | -0.80 | 69% | display_video |
| risk_targeting | strong | 0% | 0% | -0.80 | 69% | display_video |
| risk_targeting | weak | 0% | 0% | -0.80 | 69% | display_video |
| seasonal_campaign | base | 0% | 100% | 0.80 | 94% | paid_social |
| seasonal_campaign | strong | 0% | 100% | 0.80 | 94% | paid_social |
| seasonal_campaign | weak | 0% | 100% | 0.80 | 94% | paid_social |

## Interpretation

- `top_channel_recovery_rate` checks whether the model identifies the true strongest channel.
- `top2_budget_direction_overlap` checks whether the model points budget toward the correct top channels.
- `budget_efficiency_ratio` compares the true value of the model-implied channel budget direction with the true optimal direction.
- Low recovery in bundled or weak-effect scenarios means channel-level ranking should be treated as fragile, even if route-level budget recommendations remain useful.
