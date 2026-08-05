# Route-Active Baseline V0

This diagnostic model uses a logistic regression classifier with structural route features and airport-month movement context.

Important caveat: route-active labels come from a sourced manual event layer, not a complete schedule archive.

## Label Summary

- Total rows: 1,296
- Labeled rows: 894
- Label coverage: 69.0%
- Positive rate among labeled rows: 89.6%

## Temporal Holdout

| Split | N | Positive rate | Accuracy | Precision | Recall | F1 | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 693 | 89.2% | 0.993 | 1.000 | 0.992 | 0.996 | 1.000 |
| test_2025 | 201 | 91.0% | 0.945 | 0.967 | 0.973 | 0.970 | 0.851 |

## Route Label Coverage

| Route | Active | Inactive | Uncovered |
|---|---:|---:|---:|
| YHM_YEG | 47 | 0 | 25 |
| YHM_YVR | 7 | 0 | 65 |
| YHM_YYC | 13 | 0 | 59 |
| YKF_YEG | 41 | 15 | 16 |
| YKF_YHZ | 56 | 0 | 16 |
| YKF_YVR | 53 | 3 | 16 |
| YKF_YYC | 33 | 0 | 39 |
| YLW_YEG | 20 | 0 | 52 |
| YLW_YVR | 72 | 0 | 0 |
| YLW_YYC | 42 | 0 | 30 |
| YVR_YYC | 72 | 0 | 0 |
| YXU_YVR | 28 | 3 | 41 |
| YXU_YYC | 65 | 0 | 7 |
| YXX_YEG | 64 | 0 | 8 |
| YXX_YVR | 0 | 72 | 0 |
| YXX_YYC | 44 | 0 | 28 |
| YYZ_YVR | 72 | 0 | 0 |
| YYZ_YYC | 72 | 0 | 0 |

## Interpretation

- The baseline is useful as a diagnostic, not as a final route decision model.
- The next modeling improvement is to reduce uncovered route-months and avoid over-reliance on route identity proxies.
- The final portfolio narrative should emphasize data limitations and the experiment plan rather than overclaiming predictive accuracy.
