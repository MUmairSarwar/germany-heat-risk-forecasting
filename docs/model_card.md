# Model card

## Intended use

Research and education: demonstrate reproducible time-series modelling,
classification, uncertainty calibration, and climate-indicator analysis with open
German data.

## Out-of-scope use

This is **not** the official DWD heat-warning system and must not guide medical,
emergency, occupational-safety, or municipal decisions. Official warnings use
forecast data and perceived temperature, including humidity, wind, radiation, and
night-time indoor conditions.

## Evaluation

The exact holdout period and metrics are generated in `outputs/metrics.json`.
The holdout is strictly later than the model-selection and calibration periods.
The current nominal 80% conformal interval covers only 71.1% of holdout outcomes;
this undercoverage is reported as a distribution-shift diagnostic, not corrected
using holdout labels.

## Risks

- A single station misses local variation and the urban heat-island effect.
- Climate drift can reduce model accuracy and conformal coverage.
- Rare-event metrics vary substantially from year to year.
- The one-day-ahead setup uses end-of-day observations and is not an operational
  morning forecast.
