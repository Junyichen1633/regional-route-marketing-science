# MVP Scope

## MVP Principle

Start with a small route universe that is large enough to compare regional-airport decisions but small enough to debug data quality.

The MVP route list is a seed universe, not a claim that every route is currently active. Route activity should be learned from flight supply data or manually validated route histories.

## Airport Set

Regional airports:

- YKF: Waterloo Region
- YHM: Hamilton
- YXU: London
- YXX: Abbotsford
- YLW: Kelowna

Hub and benchmark airports:

- YYZ: Toronto Pearson
- YVR: Vancouver
- YYC: Calgary
- YEG: Edmonton
- YHZ: Halifax

## Why These Airports

This set creates useful contrasts:

- Southern Ontario regional airports competing with YYZ
- British Columbia regional airports competing with or feeding YVR
- Western Canada routes where low-cost carriers have historically mattered
- Hub-to-hub routes as benchmarks for broad demand cycles

## Candidate Route Roles

### Target Routes

Routes where a regional airport might consider marketing support:

- YKF to YVR, YYC, YEG, YHZ
- YHM to YVR, YYC, YEG
- YXU to YVR, YYC
- YXX to YYC, YEG
- YLW to YVR, YYC, YEG

### Benchmarks

Routes used for macro-demand and recovery context:

- YYZ to YVR
- YYZ to YYC
- YVR to YYC

### Negative Control Candidate

- YXX to YVR

This is intentionally included as a likely weak or non-commercial short-haul candidate. It can help test whether the pipeline distinguishes a realistic air route from a poor target.

## Modeling Implication

The MVP should support these route-level labels:

- `target_candidate`
- `benchmark`
- `negative_control_candidate`
- `historical_anchor`

The first model should not assume all routes are active. It should create a complete route-month skeleton, then attach observed or proxied supply data.

