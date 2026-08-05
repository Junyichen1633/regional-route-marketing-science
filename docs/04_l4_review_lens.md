# L4 Product Data Scientist Review Lens

## What an Interviewer Should See

The project should make it obvious that the analyst can work through ambiguity:

- The original user pain is specific and real.
- The business problem is generalized into a reusable decision system.
- The data constraints are identified early.
- Modeling choices follow the decision, not the other way around.
- Causal claims are bounded by evidence.
- The final recommendation is operational, not just statistical.

## Strong Signals

### Product Judgment

Good:

- "The airport needs to decide where limited marketing support changes route sustainability."

Weak:

- "I built an MMM because MMM is popular."

### Measurement Judgment

Good:

- Separate baseline demand from marketing response.
- Treat simulated marketing spend as simulation.
- Recommend experiments to validate lift.

Weak:

- Claim true marketing ROI without observed spend or calibration.

### Modeling Judgment

Good:

- Start with a baseline route model.
- Add adstock and saturation only after the business and data structure justify it.
- Use uncertainty in optimization.

Weak:

- Build a complex Bayesian model before proving the panel is usable.

### Communication

Good:

- Explain which routes to invest in, why, expected impact, and risk.

Weak:

- Only report model metrics without a decision recommendation.

## North Star Deliverable

An executive memo that says:

1. These routes are structurally healthy and likely worth scaling.
2. These routes are promising but need awareness stimulation.
3. These routes are structurally weak, so marketing alone is unlikely to save them.
4. Here is the recommended budget allocation under three budget scenarios.
5. Here is the experiment design to validate the highest-stakes recommendation.

