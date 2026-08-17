"""End-to-end experiment orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from heatrisk.config import CONFIG, ProjectConfig
from heatrisk.data import load_dwd_daily, save_processed
from heatrisk.evaluation import annual_hot_days, evaluate_forecast, theil_sen_trend
from heatrisk.features import build_supervised, split_time
from heatrisk.modeling import predict, train_bundle
from heatrisk.modeling import climatology_predict
from heatrisk.plotting import create_dashboard


def run_pipeline(config: ProjectConfig = CONFIG) -> dict:
    output_dir = Path(config.output_dir)
    model_dir = Path(config.model_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    daily = load_dwd_daily(config.station_id, config.cache_dir)
    save_processed(daily, output_dir / "darmstadt_daily.csv")
    supervised = build_supervised(daily, config.hot_day_threshold_c)
    train, validation, test = split_time(
        supervised, config.train_end, config.validation_end
    )
    bundle, validation_mae = train_bundle(
        train, validation, config.interval_coverage, config.random_seed
    )
    predictions = predict(bundle, test)
    metrics = evaluate_forecast(predictions)
    available = test["current_TXK"].notna()
    selected_available_mae = float(
        (predictions.loc[available, "predicted_tmax_c"] - test.loc[available, "target_tmax"])
        .abs()
        .mean()
    )
    persistence_mae = float(
        (test.loc[available, "current_TXK"] - test.loc[available, "target_tmax"])
        .abs()
        .mean()
    )
    metrics.update(
        {
            "persistence_comparison_days": int(available.sum()),
            "persistence_mae_c": persistence_mae,
            "selected_mae_on_persistence_days_c": selected_available_mae,
            "mae_improvement_vs_persistence_pct": float(
                100 * (persistence_mae - selected_available_mae) / persistence_mae
            ),
            "seasonal_climatology_mae_c": float(
                (
                    climatology_predict(test, bundle.climatology)
                    - test["target_tmax"].to_numpy()
                ).__abs__().mean()
            ),
        }
    )
    annual = annual_hot_days(daily, config.hot_day_threshold_c)
    trend = theil_sen_trend(annual, config.random_seed)

    report = {
        "project": "Rhine-Main Heat Risk Forecasting",
        "station": {"id": config.station_id, "name": config.station_name},
        "data_period": {
            "start": daily.index.min().strftime("%Y-%m-%d"),
            "end": daily.index.max().strftime("%Y-%m-%d"),
        },
        "splits": {
            "train_days": len(train),
            "validation_days": len(validation),
            "holdout_days": len(test),
        },
        "selected_model": bundle.selected_model,
        "validation_mae_c": validation_mae,
        "classifier_threshold": bundle.classifier_threshold,
        "conformal_radius_c": bundle.conformal_radius,
        "holdout_metrics": metrics,
        "trend": trend,
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    predictions.to_csv(output_dir / "holdout_predictions.csv", index=False)
    annual.to_csv(output_dir / "annual_hot_days.csv", index=False)
    joblib.dump(bundle, model_dir / "forecast_bundle.joblib")
    create_dashboard(annual, predictions, metrics, output_dir / "heat_risk_dashboard.png")

    latest = build_supervised(
        daily, config.hot_day_threshold_c, drop_unlabeled=False
    ).iloc[[-1]].copy()
    latest_prediction = bundle.regressor.predict(latest[bundle.feature_names])[0]
    latest_probability = bundle.classifier.predict_proba(latest[bundle.feature_names])[0, 1]
    latest_report = {
        "forecast_for": pd.Timestamp(latest["target_date"].iloc[0]).strftime("%Y-%m-%d"),
        "predicted_tmax_c": round(float(latest_prediction), 2),
        "interval_80_c": [
            round(float(latest_prediction - bundle.conformal_radius), 2),
            round(float(latest_prediction + bundle.conformal_radius), 2),
        ],
        "hot_day_probability": round(float(latest_probability), 4),
        "research_only": True,
    }
    (output_dir / "latest_research_forecast.json").write_text(
        json.dumps(latest_report, indent=2), encoding="utf-8"
    )
    return report
