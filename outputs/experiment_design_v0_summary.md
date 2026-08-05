# Experiment Design V0

This plan validates the `portfolio_value_500k` budget allocation.

## Scope

- Funded routes: 7
- Active-route tests: 6
- Relaunch feasibility tests: 1
- Total test budget: $500,000
- Control matches generated: 21

## Route-Level Test Plan

| Route | Budget | Design | Primary metric | Controls | Expected lift | MDE | Power readiness |
|---|---:|---|---|---|---:|---:|---|
| YKF_YEG | $100,000 | matched_route_geo_lift | route_bookings_or_booking_proxy | YHM_YEG, YHM_YYC, YHM_YVR | 917 | 4.5% | Low; use guardrail KPIs rather than definitive lift claim |
| YKF_YYC | $100,000 | matched_route_geo_lift | route_bookings_or_booking_proxy | YHM_YYC, YHM_YVR, YHM_YEG | 2,646 | 3.5% | Directional; pool with similar routes or extend test window |
| YKF_YVR | $75,000 | two_stage_capacity_gated_test | qualified_demand_signal | YXU_YVR, YHM_YVR, YHM_YYC | 1,424 | 8.0% | Feasibility only until capacity is committed |
| YXU_YYC | $75,000 | matched_route_geo_lift | route_bookings_or_booking_proxy | YHM_YYC, YHM_YEG, YHM_YVR | 1,527 | 3.7% | Directional; pool with similar routes or extend test window |
| YXX_YYC | $75,000 | matched_route_geo_lift | route_bookings_or_booking_proxy | YLW_YYC, YKF_YHZ, YLW_YEG | 2,417 | 3.5% | Medium; validate with booking or search-conversion data |
| YXX_YEG | $50,000 | incrementality_guardrail_test | route_booking_proxy_or_search_lift | YLW_YEG, YKF_YHZ, YLW_YYC | 1,798 | 2.7% | Directional; pool with similar routes or extend test window |
| YLW_YVR | $25,000 | incrementality_guardrail_test | route_booking_proxy_or_search_lift | YLW_YYC, YLW_YEG, YHM_YVR | 6,206 | 2.5% | Medium; validate with booking or search-conversion data |

## Measurement Positioning

- Active-route tests can be evaluated as matched-route or geo-lift experiments if booking/search-conversion data is available.
- Relaunch routes are capacity-gated feasibility tests; demand signals should not be called passenger lift until service is restorable.
- Public airport data alone is not enough for final incrementality measurement.
- The experiment plan is designed to specify the partner data required to validate the model.
