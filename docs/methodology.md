# Methodology

## Forecast task

At the end of day *t*, predict Darmstadt's maximum air temperature on day *t+1*
and the probability that *t+1* is a DWD-defined hot day (TXK ≥ 30°C).

## Leakage control

All predictors are known on or before day *t*: current observations, lags,
trailing rolling statistics, and Fourier seasonality terms for day *t+1*.
Observations are never randomly shuffled.

- Training: through 2022-12-31
- Validation/model selection/calibration: 2023-01-01 to 2024-12-31
- Holdout evaluation: 2025-01-01 onward

## Models

The temperature experiment compares persistence, seasonal climatology, ridge
regression, and histogram gradient boosting. The learned model with the smallest
validation MAE is selected. A class-weighted logistic regression estimates the
hot-day probability; its decision threshold maximises validation F2 so missed hot
days receive more weight than false alarms.

## Uncertainty

An 80% split-conformal interval is formed as

`[prediction - q, prediction + q]`,

where `q` is the finite-sample corrected quantile of absolute validation residuals.
This gives a distribution-free marginal coverage guarantee under exchangeability;
weather drift and serial dependence can weaken that guarantee.

## Trend

Annual hot-day counts are summarised with a Theil–Sen slope, the median of all
pairwise slopes. A deterministic bootstrap gives a descriptive 95% interval. This
is an exploratory trend, not a causal attribution study.

