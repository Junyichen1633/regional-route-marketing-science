# Data Strategy

## Preferred Unit of Analysis

```text
origin_airport x destination_airport x month
```

This is the right conceptual grain because marketing decisions are route-specific. However, public Canadian aviation data may not fully support true route-month passenger volume.

## Data Reality

### Passenger Demand

Public Statistics Canada airport passenger traffic is available at airport level and annual frequency for many airports. This is useful for context, calibration, and airport-level trend analysis, but may not provide route-month passenger counts.

Potential use:

- Airport-level demand context
- Recovery trend from COVID period
- Calibration benchmark for route proxies

### Screened Passenger Traffic

CATSA screened passenger traffic has monthly frequency but is focused on Canada's largest airports. It is useful for national or hub-airport context, but less useful for regional airports like YKF, YHM, or YXU.

### Route Activity and Supply

Route-level monthly activity may need to be proxied through:

- Flight schedules
- Flight frequency
- OpenSky airport departures/arrivals
- Public airline route announcements
- Historical route availability
- Airport annual reports if available
- Statistics Canada airport-month aircraft movements

Important caveat:

OpenSky can provide flight arrival/departure records by airport through its API, but public endpoint limits and historical availability may require careful sampling or authentication.

Current project finding:

Statistics Canada Table 23-10-0302-01 provides monthly airport-level movements for every MVP airport. It does not identify destination airport, but it is usable as a supply/activity context feature.

### Weather

Environment and Climate Change Canada provides historical weather data, including daily and monthly climate observations depending on station coverage.

Potential features:

- Snow days
- Precipitation
- Mean temperature
- Extreme weather indicators
- Weather disruption proxy

### Demand Signals

Google Trends can be used as a directional search-interest proxy.

Important caveats:

- Values are normalized indices, not search volume.
- Low-volume searches may be noisy or zero.
- It should not be treated as exact demand.

### Marketing Spend

Real marketing spend is not expected to be publicly available.

Options:

1. Observed spend if a partner dataset becomes available.
2. Synthetic route-level marketing budgets based on realistic planning rules.
3. Scenario-based response simulator without claiming observed attribution.

Recommended approach for this portfolio project:

Use synthetic spend only for the marketing response and optimization module, clearly label it as scenario-based, and focus the causal story on how the recommendation would be validated through experiments.

## MVP Dataset Definition

Minimum viable table:

- route_id
- origin_airport
- destination_airport
- month
- route_active
- flight_frequency_proxy
- airport_traffic_context
- weather_features
- holiday_features
- distance_features
- competition_features
- macro_features
- simulated_marketing_spend
- simulated_incremental_passengers

## Data Source Priority

1. Statistics Canada aviation tables
2. Environment and Climate Change Canada weather data
3. OpenSky or alternative flight activity source
4. Google Trends manual exports or documented proxy
5. Public airport and airline route announcements
6. Synthetic marketing plan assumptions

## Feasibility Decision

The project should proceed even if true route-month passenger counts are unavailable, but the outcome variable must be named honestly:

- Best case: `monthly_passengers`
- Acceptable proxy: `route_active`, `route_activity`, `flight_frequency`, or `estimated_seats`
- Simulation component: `simulated_incremental_passengers`

After Phase 1 feasibility work, the recommended MVP target is `route_active` or a route opportunity score, not observed route-month passengers.
