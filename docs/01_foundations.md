# Foundations to Understand Before Modeling

## 1. Business Layer

### Route Sustainability

A route disappears when expected profit, strategic value, or operational fit falls below the airline's threshold. Passenger demand matters, but it is not the only driver.

Important route-level drivers:

- Passenger demand
- Flight frequency and seat capacity
- Aircraft availability
- Yield and fare mix
- Airport fees and operating costs
- Seasonality
- Competition from nearby hub airports
- Connection opportunities
- Weather and disruption risk
- Marketing and local awareness

For this project, the key decision is not "why did one route disappear?" but "which routes are worth supporting with limited marketing dollars?"

## 2. Demand vs Supply

Observed passengers are not pure demand. They are constrained by supply.

Example:

- If a route has only two flights per week, passenger volume may look low even when latent demand is higher.
- If an airline removes capacity, passengers may shift to YYZ or YVR rather than disappear.

So the baseline model should include supply features such as route availability, flight frequency, and estimated seats.

## 3. Baseline Demand Model

The baseline model estimates what demand or route activity would look like without incremental marketing.

Candidate approaches:

- Panel regression with route and month fixed effects
- Mixed-effects model with airport and route random effects
- Gradient boosting for prediction
- Time-series cross-validation by route

The baseline model should answer:

- Which routes are structurally healthy?
- Which routes are seasonal?
- Which routes are exposed to nearby hub competition?
- Which routes are declining even before marketing assumptions?

## 4. MMM as a Component

Marketing Mix Modeling estimates the relationship between aggregated marketing inputs and an aggregate outcome. It usually includes:

- Outcome: revenue, conversions, passengers, bookings, or route activity
- Media variables: spend, impressions, clicks, GRPs, or campaign pressure
- Controls: seasonality, price, competitor activity, macro factors, holidays
- Transformations: adstock and saturation

In this project, MMM should not be the primary model because real marketing spend is not expected to be publicly available. Instead, MMM logic is used inside a marketing response module.

## 5. Adstock

Adstock models delayed marketing effects.

If a campaign runs this month, some of its effect may carry into future months. A simple geometric adstock can be written as:

```text
adstock_t = spend_t + decay * adstock_{t-1}
```

Higher decay means the effect lasts longer.

## 6. Saturation

Saturation models diminishing returns.

Early marketing spend may produce strong incremental demand, but after enough spend the route audience becomes harder to expand.

Common response curve intuition:

- Low spend: high marginal return
- Medium spend: useful incremental growth
- High spend: flattening response

## 7. Google Meridian

Google Meridian is an open-source Bayesian MMM framework. It is useful when the project needs:

- Uncertainty intervals
- Priors
- Geo-level modeling
- Calibration with experiments or prior knowledge
- ROI and response curves
- Budget optimization

For this project, Meridian is best treated as the advanced MMM component after the route-month dataset and marketing assumptions are ready.

## 8. Optimization

The optimizer should not simply maximize total passengers. Better objectives include:

- Incremental passengers
- Incremental contribution margin
- Probability of route sustainability
- Marginal ROI
- Weighted portfolio score

The strongest framing is:

> Allocate budget to maximize expected route sustainability subject to total budget, route caps, minimum spend, and uncertainty constraints.

## 9. Experiment Design

Model recommendations need validation.

Realistic experiment designs:

- Geo lift: promote selected routes or markets, compare to control markets
- Difference-in-differences: compare treated routes before and after campaign versus similar untreated routes
- Synthetic control: build a weighted control route/airport benchmark
- Matched-market test: pair similar routes and vary campaign intensity

Switchback is less realistic for monthly airline route marketing because demand cycles and booking windows are too long.

## 10. Portfolio Narrative

The project should show that the analyst can:

- Translate a personal observation into a business problem
- Identify data limitations honestly
- Separate demand, supply, and marketing effects
- Build a model that supports decisions
- Recommend experiments instead of overclaiming causality

