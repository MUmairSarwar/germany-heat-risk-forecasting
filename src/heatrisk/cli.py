"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from heatrisk.config import CONFIG
from heatrisk.data import load_dwd_daily, save_processed
from heatrisk.evaluation import evaluate_forecast
from heatrisk.pipeline import run_pipeline
from heatrisk.plotting import create_dashboard


def _demo(output_dir: Path) -> dict:
    """Offline CI smoke test using deterministic synthetic predictions."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-01-01", periods=120, freq="D")
    observed = 18 + 9 * np.sin(np.linspace(-1.5, 1.5, len(dates))) + rng.normal(0, 1, len(dates))
    predicted = observed + rng.normal(0, 1.6, len(dates))
    frame = pd.DataFrame(
        {
            "target_date": dates,
            "observed_tmax_c": observed,
            "predicted_tmax_c": predicted,
            "lower_80_c": predicted - 2.1,
            "upper_80_c": predicted + 2.1,
            "observed_hot_day": (observed >= 25).astype(int),
            "hot_day_probability": np.clip((predicted - 21) / 8, 0, 1),
            "predicted_hot_day": (predicted >= 25).astype(int),
        }
    )
    annual = pd.DataFrame({"year": range(1996, 2026), "hot_days": np.arange(30) // 3 + 3})
    metrics = evaluate_forecast(frame)
    create_dashboard(annual, frame, metrics, output_dir / "demo_dashboard.png")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Darmstadt heat-risk forecasting")
    parser.add_argument("command", choices=["download", "run", "demo"], nargs="?", default="run")
    parser.add_argument("--output-dir", type=Path, default=CONFIG.output_dir)
    args = parser.parse_args()

    if args.command == "download":
        daily = load_dwd_daily(CONFIG.station_id, CONFIG.cache_dir)
        save_processed(daily, args.output_dir / "darmstadt_daily.csv")
        print(f"Saved {len(daily):,} observations through {daily.index.max().date()}")
    elif args.command == "demo":
        print(json.dumps(_demo(args.output_dir), indent=2))
    else:
        report = run_pipeline(replace(CONFIG, output_dir=args.output_dir))
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

