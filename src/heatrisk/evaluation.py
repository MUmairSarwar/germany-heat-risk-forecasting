"""Metrics and robust trend estimation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_forecast(predictions: pd.DataFrame) -> dict[str, float | int]:
    observed = predictions["observed_tmax_c"]
    predicted = predictions["predicted_tmax_c"]
    hot = predictions["observed_hot_day"]
    hot_hat = predictions["predicted_hot_day"]
    probability = predictions["hot_day_probability"]
    covered = (
        (observed >= predictions["lower_80_c"])
        & (observed <= predictions["upper_80_c"])
    )
    metrics: dict[str, float | int] = {
        "holdout_days": int(len(predictions)),
        "holdout_hot_days": int(hot.sum()),
        "temperature_mae_c": float(mean_absolute_error(observed, predicted)),
        "temperature_rmse_c": float(mean_squared_error(observed, predicted) ** 0.5),
        "interval_80_coverage": float(covered.mean()),
        "interval_mean_width_c": float(
            (predictions["upper_80_c"] - predictions["lower_80_c"]).mean()
        ),
        "hot_day_precision": float(precision_score(hot, hot_hat, zero_division=0)),
        "hot_day_recall": float(recall_score(hot, hot_hat, zero_division=0)),
        "hot_day_f1": float(f1_score(hot, hot_hat, zero_division=0)),
        "hot_day_brier": float(brier_score_loss(hot, probability)),
        "hot_day_pr_auc": float(average_precision_score(hot, probability)),
    }
    if hot.nunique() == 2:
        metrics["hot_day_roc_auc"] = float(roc_auc_score(hot, probability))
    return metrics


def annual_hot_days(daily: pd.DataFrame, threshold: float = 30.0) -> pd.DataFrame:
    valid_counts = daily["TXK"].notna().groupby(daily.index.year).sum()
    complete_years = valid_counts[valid_counts >= 350].index
    complete = daily[daily.index.year.isin(complete_years)].copy()
    annual = (complete["TXK"] >= threshold).groupby(complete.index.year).sum().astype(int)
    return annual.rename("hot_days").rename_axis("year").reset_index()


def theil_sen_trend(
    annual: pd.DataFrame, seed: int = 42, bootstrap_samples: int = 2000
) -> dict[str, float]:
    years = annual["year"].to_numpy(dtype=float)
    values = annual["hot_days"].to_numpy(dtype=float)
    slopes = [
        (values[j] - values[i]) / (years[j] - years[i])
        for i in range(len(years))
        for j in range(i + 1, len(years))
        if years[j] != years[i]
    ]
    estimate = float(np.median(slopes))
    rng = np.random.default_rng(seed)
    bootstrap: list[float] = []
    for _ in range(bootstrap_samples):
        indices = rng.integers(0, len(years), len(years))
        sample = pd.DataFrame({"year": years[indices], "value": values[indices]})
        sample = sample.groupby("year", as_index=False)["value"].mean().sort_values("year")
        if len(sample) > 1:
            sample_years = sample["year"].to_numpy()
            sample_values = sample["value"].to_numpy()
            sample_slopes = [
                (sample_values[j] - sample_values[i])
                / (sample_years[j] - sample_years[i])
                for i in range(len(sample_years))
                for j in range(i + 1, len(sample_years))
                if sample_years[j] != sample_years[i]
            ]
            bootstrap.append(float(np.median(sample_slopes)))
    low, high = np.quantile(bootstrap, [0.025, 0.975])
    return {
        "theil_sen_hot_days_per_year": estimate,
        "bootstrap_slope_ci_95_low": float(low),
        "bootstrap_slope_ci_95_high": float(high),
    }
