# Rhine–Main Heat Risk Forecasting

[![CI](https://github.com/MUmairSarwar/germany-heat-risk-forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/MUmairSarwar/germany-heat-risk-forecasting/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reproducible data-science project that predicts next-day heat risk in Darmstadt,
Germany, from official Deutscher Wetterdienst (DWD) observations. It combines
time-series feature engineering, model comparison, rare-event classification,
split-conformal uncertainty intervals, and a robust trend estimator.

![Heat-risk analytical dashboard](outputs/heat_risk_dashboard.png)

## Why this problem matters

The DWD defines a **hot day** as one with a maximum air temperature of at least
30°C. German environmental authorities use hot days and tropical nights to assess
heat-related health burden. A transparent local model is a useful research case
for studying early warning, uncertainty, climate drift, and rare events.

This repository is a research project—not an official DWD warning service.

## Research questions

1. Can simple, reproducible models improve on persistence and seasonal climatology
   for next-day maximum-temperature prediction?
2. How reliably can tomorrow's DWD-defined hot day be detected?
3. Do 80% split-conformal intervals achieve their intended coverage on later data?
4. How has the annual number of hot days changed at station 00917 since 1995?

## What makes the project research-ready

- Real German public-sector data, downloaded directly from DWD CDC
- Strict chronological train/validation/holdout design
- Four transparent regression benchmarks
- Cost-sensitive hot-day classification with validation-only threshold selection
- Finite-sample split-conformal prediction intervals
- Robust Theil–Sen trend estimation with bootstrap uncertainty
- Automated tests, offline CI smoke test, model/data cards, and deterministic seeds

## Current results

The checked-in experiment uses observations through **2026-08-16** and a strict
2025+ holdout containing 558 days and 66 hot days.

| Holdout result | Value |
|---|---:|
| Selected model | Histogram gradient boosting |
| Maximum-temperature MAE | 2.28°C |
| Improvement over persistence | 10.3% |
| Hot-day recall | 98.5% |
| Hot-day precision | 52.8% |
| Hot-day PR AUC | 0.767 |
| Nominal 80% interval coverage | 71.1% |
| Robust hot-day trend | +0.42 days/year |

The interval's 71.1% holdout coverage is below its 80% target. That failure is kept
visible rather than hidden: it is evidence that exchangeability is imperfect under
weather/climate drift and that operational calibration would need monitoring or
rolling updates. Exact values are generated in
[`outputs/metrics.json`](outputs/metrics.json).

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
heat-risk run
```

The run downloads and caches the latest historical and recent daily archives for
DWD station 00917. Outputs:

- `outputs/metrics.json` — experiment summary and holdout metrics
- `outputs/holdout_predictions.csv` — auditable daily predictions
- `outputs/annual_hot_days.csv` — annual climate indicator
- `outputs/heat_risk_dashboard.png` — four-panel analytical figure
- `outputs/latest_research_forecast.json` — latest research prediction
- `models/forecast_bundle.joblib` — fitted model bundle (ignored by Git)

## Repository structure

```text
src/heatrisk/        tested Python package
tests/               unit tests for data, leakage, and calibration
docs/                methodology, model card, and data card
outputs/             generated metrics, predictions, and dashboard
.github/workflows/   CI pipeline
```

## Mathematical notes

The feature map includes lagged weather, trailing moments, and three Fourier
harmonics for annual seasonality. Ridge regression controls coefficient variance;
gradient boosting captures nonlinear interactions. The uncertainty band uses a
calibration quantile of absolute residuals, while the climate trend uses the median
of pairwise annual slopes. See [`docs/methodology.md`](docs/methodology.md).

## Data and attribution

Source: **Deutscher Wetterdienst (DWD), Climate Data Center**, station 00917
Darmstadt. DWD makes climate data available on its Open Data server. Variable
definitions and limitations are documented in [`docs/data_card.md`](docs/data_card.md).

## Other selected projects

- [Retail Customer & Operations Analytics](https://github.com/MUmairSarwar/retail-customer-analytics)
- [Telecom Customer Churn Prediction](https://github.com/MUmairSarwar/customer-churn-prediction)
- [Robust Federated Learning](https://github.com/MUmairSarwar/robust-federated-learning-ml-security)
- [Strategic Classification](https://github.com/MUmairSarwar/strategic-classification-toy)

## Author

Muhammad Umair Sarwar - M.Sc. Mathematics student (Mathematics in Data Science), TU Darmstadt.
