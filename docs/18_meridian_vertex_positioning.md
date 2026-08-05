# Meridian and Vertex AI Positioning

## Short Answer

This project does not currently run Google Meridian.

Meridian is positioned as a future MMM component that could replace the scenario-based marketing response module after real route-level marketing spend and outcome data become available.

Vertex AI is positioned as the future production platform for pipeline orchestration, experiment tracking, model comparison, and scheduled scoring.

## What Meridian Is

Google Meridian is an open-source Marketing Mix Modeling framework. It is implemented as a Python library/package, distributed as `google-meridian`, and is designed for building, running, analyzing, calibrating, and optimizing MMMs.

In practical terms:

- It is not the same thing as Vertex AI.
- It is not just a model artifact.
- It is a modeling framework/library for MMM workflows.
- It can estimate channel contribution, ROI, marginal ROI, response curves, and budget optimization when valid media and outcome data exist.

## Why It Is Not Used Directly Yet

This project uses public route and airport data. It does not have observed route-level:

- channel spend
- impressions or reach/frequency
- route bookings
- search-to-booking conversions
- load factor
- fare or yield

Because those variables are not observed, directly fitting Meridian would create a false sense of precision. The project therefore keeps the marketing response layer scenario-based and labels passenger outcomes as proxies.

## Where Meridian Would Fit

Current workflow:

```text
route-month panel
-> route supply model
-> route opportunity score
-> scenario-based marketing response
-> sensitivity/recovery analysis
-> constrained budget optimizer
-> experiment design
```

Future workflow with partner data:

```text
route-month panel with real spend and outcomes
-> route supply model
-> route opportunity score
-> Meridian MMM response model
-> calibrated response curves and ROI/mROI
-> constrained budget optimizer
-> experiment design and refresh loop
```

## Recommended Framing

The right phrasing is:

> I did not claim to run a production MMM because the available data does not support that. I built the route-level decision workflow first, then treated Meridian as the production-grade MMM component I would plug in once real spend and booking outcomes are available.

That is stronger than saying:

> I used Meridian.

The project's credibility comes from knowing when not to overclaim.
