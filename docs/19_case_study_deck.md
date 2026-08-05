# Phase 7C Case Study Deck

## Objective

Create an interview-ready PowerPoint deck that explains the project as an L4 product data science case study.

The deck is designed to answer:

- What is the business decision?
- Why is this not framed as a pure MMM project?
- How does the route demand/supply layer connect to marketing response?
- What did sensitivity analysis prove and not prove?
- What budget allocation is recommended?
- How should the recommendation be validated?
- Where would Google Meridian and Vertex AI fit in a production version?

## Output

```text
presentations/regional_route_marketing_science_case_study.pptx
```

## Builder

```text
src/build_case_study_deck.mjs
```

The builder reads the latest generated CSV outputs and creates an editable PPTX with native charts, text, and table-like objects.

## Slide Outline

1. Title
2. Business decision and operating constraints
3. Three-layer workflow
4. Route opportunity score and route network
5. Marketing sensitivity and recovery analysis
6. Recommended CAD 500K allocation
7. Validation design
8. Meridian and Vertex AI production path

## Meridian Clarification

The deck explicitly says the project did not run Google Meridian.

Meridian is positioned as the future MMM component that would replace the scenario-based response module after real route-level spend and outcome data exist.

Vertex AI is positioned as the future production platform for pipeline orchestration, model comparison, scheduled scoring, and experiment tracking.

## Validation

Completed checks:

- PPTX exported successfully.
- 8 slides generated.
- All slides rendered to PNG previews.
- `slides_test.py` passed with no overflow detected.
- Sensitivity chart was checked against `marketing_sensitivity_summary_v0.csv`.
- Speaker notes include source blocks for project artifacts and external Meridian references.

## QA Note

The rendered previews are stored under:

```text
work/deck_build/rendered/
```

The `work/` directory is intentionally ignored by git because it contains temporary rendering artifacts and local toolchain files.
