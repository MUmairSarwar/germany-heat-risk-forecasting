"""Leakage-safe feature engineering for one-day-ahead forecasts."""

from __future__ import annotations

import numpy as np
import pandas as pd

WEATHER_COLUMNS = ["TXK", "TNK", "TMK", "UPM", "RSK", "SDK", "VPM"]


def build_supervised(
    daily: pd.DataFrame,
    hot_threshold: float = 30.0,
    drop_unlabeled: bool = True,
) -> pd.DataFrame:
    """Create features known on day t and targets for day t+1."""
    missing = sorted(set(WEATHER_COLUMNS) - set(daily.columns))
    if missing:
        raise ValueError(f"Missing weather columns: {missing}")

    data = daily.sort_index().copy()
    features = pd.DataFrame(index=data.index)
    for column in WEATHER_COLUMNS:
        features[f"current_{column}"] = data[column]

    for lag in (1, 2, 3, 7, 14):
        for column in ("TXK", "TNK", "TMK", "UPM"):
            features[f"{column}_lag_{lag}"] = data[column].shift(lag)

    for window in (3, 7, 14):
        for column in ("TXK", "TNK", "TMK"):
            features[f"{column}_mean_{window}"] = data[column].rolling(window).mean()
            features[f"{column}_std_{window}"] = data[column].rolling(window).std()

    target_date = features.index + pd.Timedelta(days=1)
    day = target_date.dayofyear.to_numpy()
    for harmonic in (1, 2, 3):
        angle = 2.0 * np.pi * harmonic * day / 365.2425
        features[f"sin_doy_{harmonic}"] = np.sin(angle)
        features[f"cos_doy_{harmonic}"] = np.cos(angle)
    features["year_trend"] = target_date.year.to_numpy() - target_date.year.min()

    next_max = data["TXK"].shift(-1)
    features["target_date"] = target_date
    features["target_tmax"] = next_max
    features["target_hot_day"] = (next_max >= hot_threshold).astype(float)
    features.loc[next_max.isna(), "target_hot_day"] = np.nan
    features = features.iloc[14:].copy()
    if drop_unlabeled:
        features = features.dropna(subset=["target_tmax"])
    return features


def split_time(
    supervised: pd.DataFrame,
    train_end: str = "2022-12-31",
    validation_end: str = "2024-12-31",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    target_date = pd.to_datetime(supervised["target_date"])
    train = supervised[target_date <= pd.Timestamp(train_end)].copy()
    validation = supervised[
        (target_date > pd.Timestamp(train_end))
        & (target_date <= pd.Timestamp(validation_end))
    ].copy()
    test = supervised[target_date > pd.Timestamp(validation_end)].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("One or more chronological splits are empty")
    return train, validation, test


def feature_columns(supervised: pd.DataFrame) -> list[str]:
    excluded = {"target_date", "target_tmax", "target_hot_day"}
    return [column for column in supervised.columns if column not in excluded]
