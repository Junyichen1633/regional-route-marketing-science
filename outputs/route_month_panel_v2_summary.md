# Route-Month Panel V2 Summary

- Rows: 1,296
- Routes: 18
- Active route-month labels: 801
- Inactive route-month labels: 93
- Uncovered route-month labels: 402
- Route-active coverage: 69.0%

| Field | Non-empty share |
|---|---:|
| route_active | 69.0% |
| direct_weekly_frequency_proxy | 44.4% |
| route_supply_confidence | 100.0% |
| origin_domestic_air_carrier_all_levels_movements | 100.0% |
| destination_domestic_air_carrier_all_levels_movements | 100.0% |
| nearest_origin_hub_domestic_air_carrier_all_levels_movements | 100.0% |

Modeling guidance:

- Use rows with non-empty `route_active` for a first route-active classifier.
- Treat `uncovered` rows as missing labels, not negatives.
- `direct_weekly_frequency_proxy` is an evidence-based proxy, not a complete observed schedule archive.
