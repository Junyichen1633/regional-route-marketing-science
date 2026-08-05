# Project Plan

## Phase 0: Scope and Decision Memo

Goal: define exactly what decision the model supports.

Deliverables:

- Business problem statement
- Candidate route list
- Decision owner and decision cadence
- Success metrics
- Data limitation memo

Exit criteria:

- We can explain the project in two minutes to a business or technical reviewer.

## Phase 1: Data Inventory and Feasibility

Goal: determine which public datasets can support the project.

Tasks:

- Inventory airport-level traffic data
- Inventory route or flight-frequency data
- Inventory weather data
- Inventory macro and holiday data
- Decide whether route-month passenger volume is directly available or must be proxied

Deliverables:

- Data source table
- Data quality notes
- MVP data schema
- Fallback plan if route-level passenger volume is unavailable

Exit criteria:

- We know the target unit of analysis and the outcome variable.

## Phase 2: Route-Month Panel

Goal: build the core modeling table.

Target grain:

```text
origin_airport x destination_airport x month
```

Candidate columns:

- route_id
- origin_airport
- destination_airport
- month
- route_active
- flight_frequency
- estimated_seats
- passenger_proxy
- airport_traffic
- distance_km
- nearest_hub_distance
- weather_features
- holiday_features
- search_interest
- fuel_price
- macro_features

Deliverables:

- Clean panel dataset
- Data dictionary
- Missingness report

Exit criteria:

- A notebook can load the panel and reproduce summary stats.

## Phase 3: Baseline Route Demand and Supply Model

Goal: estimate route health before marketing intervention.

Candidate models:

- Fixed-effects regression
- Mixed-effects regression
- Gradient boosting baseline

Outputs:

- Predicted baseline route activity
- Route health score
- Key drivers
- Forecast error by route

Exit criteria:

- We can rank routes by baseline sustainability.

## Phase 4: Marketing Response Module

Goal: estimate or simulate incremental demand from marketing.

Approach:

- If real marketing spend is available, fit MMM with Meridian.
- If not, use transparent simulated spend scenarios and response curves.
- Include adstock and saturation assumptions.
- Run sensitivity analysis across optimistic, base, and conservative response assumptions.

Outputs:

- Incremental passengers by route
- Marginal response curves
- ROI by route
- Uncertainty ranges

Exit criteria:

- We can explain which routes are most responsive to marketing and why.

## Phase 5: Budget Optimization

Goal: recommend budget allocation.

Candidate objective:

```text
maximize expected incremental contribution margin
subject to:
  total budget <= B
  route_min <= spend_route <= route_max
  risk constraint
  operational constraints
```

Alternative objectives:

- Maximize incremental passengers
- Maximize route sustainability score
- Maximize ROI subject to minimum route support

Outputs:

- Recommended spend by route
- Expected lift
- Marginal ROI
- No-invest / maintain / scale recommendations

Exit criteria:

- The optimizer produces interpretable recommendations under multiple budget scenarios.

## Phase 6: Experiment Recommendation

Goal: validate the model's highest-value recommendations.

Deliverables:

- Suggested geo lift or matched-route test
- Treatment/control design
- Power and sample-size considerations
- Success metric
- Risks and guardrails

Exit criteria:

- We can describe how the airport or airline would test the recommendation in the real world.

## Phase 7: Portfolio Packaging

Goal: make the work easy to evaluate.

Deliverables:

- Executive memo
- Technical methodology writeup
- Notebook walkthrough
- Visual route portfolio
- Budget simulator output

Exit criteria:

- A reviewer can understand the business value, technical choices, assumptions, and limitations without reading every line of code.
