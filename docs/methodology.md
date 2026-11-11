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

A nominal 80% interval using a split-conformal calibration recipe is formed as

`[prediction - q, prediction + q]`,

where `q` is the finite-sample corrected quantile of absolute validation residuals.
The validation period also selects the regression model, so calibration is not
independent of that selection. Daily weather is serially dependent and can drift.
The standard marginal-coverage guarantee does not apply to this experiment;
the held-out coverage is the reported measure.

## Trend

Annual hot-day counts are summarised with a Theil–Sen slope, the median of all
pairwise slopes. A deterministic bootstrap gives a descriptive 95% interval. This
is an exploratory trend, not a causal attribution study.

