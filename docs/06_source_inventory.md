# Source Inventory

This file tracks candidate public sources and how each source should be used in the project.

## Aviation Demand and Context

### Statistics Canada: Air Passenger Traffic at Canadian Airports

- URL: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2310025301
- Table: 23-10-0253-01
- Frequency: Annual
- Use: airport-level passenger context and calibration benchmark
- Limitation: not route-month passenger demand

### Statistics Canada: Screened Passenger Traffic at Largest Airports

- URL: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2310031201
- Table: 23-10-0312-01
- Frequency: Monthly
- Use: national and hub-airport demand context
- Limitation: focused on Canada's largest airports, not enough for most regional-airport route modeling

## Flight Supply and Route Activity

### Statistics Canada: Domestic and International Itinerant Movements by Type of Operation

- URL: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2310030201
- Table: 23-10-0302-01
- Frequency: Monthly
- Use: airport-level supply/activity proxy for every MVP airport
- Limitation: identifies airport and movement type, but not destination airport

### OpenSky Network API

- URL: https://openskynetwork.github.io/opensky-api/rest.html
- Use: route activity and airport arrivals/departures proxy
- Limitation: endpoint windows, authentication, rate limits, and historical coverage need validation
- Current project status: a CYKF departure probe returned HTTP 403, so anonymous access is not reliable for this MVP

## Weather

### Environment and Climate Change Canada Historical Climate Data

- URL: https://climat.weather.gc.ca/historical_data/search_historic_data_e.html
- Use: historical weather features near origin and destination airports
- Candidate features: temperature, precipitation, snow, extreme weather, disruption proxy
- Limitation: station coverage and interval availability vary by station

## Demand Signals

### Google Trends

- URL: https://support.google.com/trends/answer/4365533
- Use: search-interest proxy for destination or route demand
- Limitation: normalized index, sampling/noise, not actual search volume

## MMM Frameworks

### Google Meridian

- URL: https://developers.google.com/meridian/mmm
- Use: preferred Bayesian MMM component for marketing response modeling when data supports it
- Strengths: Bayesian uncertainty, calibration, response curves, budget optimization, geo-level modeling
- Limitation: requires proper media/input data; GPU recommended for heavier runs

### Meta Robyn

- URL: https://github.com/facebookexperimental/robyn
- Use: alternative MMM reference, especially for adstock/saturation and budget allocator concepts
- Strengths: mature open-source MMM workflow, automated search, budget allocator
- Limitation: Python implementation is less mature than R; not the primary project choice

## Important Modeling Rule

If real marketing spend is unavailable, the project must not claim observed marketing attribution. It should describe the marketing module as:

```text
scenario-based marketing response simulation
```

The causal validation story should come from proposed experiments.
