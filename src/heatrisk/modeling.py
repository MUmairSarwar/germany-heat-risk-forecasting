"""Regression, classification, calibration, and model-selection routines."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.metrics import fbeta_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from heatrisk.features import feature_columns


@dataclass
class ForecastBundle:
    regressor: object
    classifier: Pipeline
    classifier_threshold: float
    conformal_radius: float
    selected_model: str
    feature_names: list[str]
    climatology: dict[int, float]


def _ridge() -> TransformedTargetRegressor:
    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", RidgeCV(alphas=np.logspace(-3, 3, 25))),
        ]
    )
    return TransformedTargetRegressor(regressor=pipeline, transformer=StandardScaler())


def _boosting(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                HistGradientBoostingRegressor(
                    learning_rate=0.05,
                    max_iter=300,
                    max_leaf_nodes=15,
                    min_samples_leaf=20,
                    l2_regularization=1.0,
                    random_state=seed,
                ),
            ),
        ]
    )


def _conformal_radius(residuals: np.ndarray, coverage: float) -> float:
    if not 0.0 < coverage < 1.0:
        raise ValueError("Coverage must lie strictly between zero and one")
    n = len(residuals)
    level = min(1.0, np.ceil((n + 1) * coverage) / n)
    return float(np.quantile(np.abs(residuals), level, method="higher"))


def _climatology(train: pd.DataFrame) -> dict[int, float]:
    return (
        train.assign(doy=pd.to_datetime(train["target_date"]).dt.dayofyear)
        .groupby("doy")["target_tmax"]
        .mean()
        .to_dict()
    )


def climatology_predict(frame: pd.DataFrame, mapping: dict[int, float]) -> np.ndarray:
    days = pd.to_datetime(frame["target_date"]).dt.dayofyear
    fallback = float(np.mean(list(mapping.values())))
    return days.map(mapping).fillna(fallback).to_numpy()


def train_bundle(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    coverage: float = 0.80,
    seed: int = 42,
) -> tuple[ForecastBundle, dict[str, float]]:
    columns = [column for column in feature_columns(train) if train[column].notna().any()]
    x_train, y_train = train[columns], train["target_tmax"]
    x_val, y_val = validation[columns], validation["target_tmax"]

    candidates = {"ridge": _ridge(), "hist_gradient_boosting": _boosting(seed)}
    validation_mae: dict[str, float] = {}
    fitted: dict[str, object] = {}
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        fitted[name] = model
        validation_mae[name] = float(mean_absolute_error(y_val, model.predict(x_val)))

    validation_mae["persistence"] = float(
        mean_absolute_error(y_val, validation["current_TXK"])
    )
    climatology = _climatology(train)
    validation_mae["seasonal_climatology"] = float(
        mean_absolute_error(y_val, climatology_predict(validation, climatology))
    )

    model_names = list(candidates)
    selected_name = min(model_names, key=validation_mae.get)
    selected = fitted[selected_name]
    val_prediction = selected.predict(x_val)
    radius = _conformal_radius(y_val.to_numpy() - val_prediction, coverage)

    classifier = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced", max_iter=2000, random_state=seed
                ),
            ),
        ]
    )
    classifier.fit(x_train, train["target_hot_day"].astype(int))
    val_probability = classifier.predict_proba(x_val)[:, 1]
    thresholds = np.linspace(0.05, 0.95, 181)
    f2 = [
        fbeta_score(
            validation["target_hot_day"].astype(int),
            (val_probability >= threshold).astype(int),
            beta=2,
            zero_division=0,
        )
        for threshold in thresholds
    ]
    threshold = float(thresholds[int(np.argmax(f2))])

    bundle = ForecastBundle(
        regressor=selected,
        classifier=classifier,
        classifier_threshold=threshold,
        conformal_radius=radius,
        selected_model=selected_name,
        feature_names=columns,
        climatology=climatology,
    )
    return bundle, validation_mae


def predict(bundle: ForecastBundle, frame: pd.DataFrame) -> pd.DataFrame:
    point = bundle.regressor.predict(frame[bundle.feature_names])
    probability = bundle.classifier.predict_proba(frame[bundle.feature_names])[:, 1]
    return pd.DataFrame(
        {
            "target_date": pd.to_datetime(frame["target_date"]).to_numpy(),
            "observed_tmax_c": frame["target_tmax"].to_numpy(),
            "predicted_tmax_c": point,
            "lower_80_c": point - bundle.conformal_radius,
            "upper_80_c": point + bundle.conformal_radius,
            "observed_hot_day": frame["target_hot_day"].astype(int).to_numpy(),
            "hot_day_probability": probability,
            "predicted_hot_day": (probability >= bundle.classifier_threshold).astype(int),
        },
        index=frame.index,
    )
