"""Generate a compact, recruiter-friendly analytical dashboard."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def create_dashboard(
    annual: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics: dict,
    path: Path | str,
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        "Darmstadt Heat Risk: Trend and One-Day-Ahead Forecasting",
        fontsize=17,
        fontweight="bold",
    )

    ax = axes[0, 0]
    ax.bar(annual["year"], annual["hot_days"], color="#ef8354", alpha=0.8)
    fit = np.polyfit(annual["year"], annual["hot_days"], 1)
    ax.plot(annual["year"], np.polyval(fit, annual["year"]), color="#b12a5b", linewidth=2)
    ax.set(title="Annual DWD hot days (TX ≥ 30°C)", ylabel="Days")

    ax = axes[0, 1]
    recent_raw = predictions.tail(min(180, len(predictions))).copy()
    recent = (
        recent_raw.set_index("target_date")
        .reindex(pd.date_range(recent_raw["target_date"].min(), recent_raw["target_date"].max()))
        .rename_axis("target_date")
        .reset_index()
    )
    ax.fill_between(
        recent["target_date"],
        recent["lower_80_c"],
        recent["upper_80_c"],
        color="#80b1d3",
        alpha=0.3,
        label="80% conformal interval",
    )
    ax.plot(recent["target_date"], recent["observed_tmax_c"], color="#22223b", label="Observed")
    ax.plot(recent["target_date"], recent["predicted_tmax_c"], color="#3a86ff", label="Forecast")
    ax.axhline(30, color="#d62828", linestyle="--", linewidth=1.5, label="Hot-day threshold")
    ax.set(title="Latest holdout forecasts", ylabel="Maximum temperature (°C)")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1, 0]
    ax.scatter(
        predictions["observed_tmax_c"],
        predictions["predicted_tmax_c"],
        c=predictions["observed_hot_day"],
        cmap="coolwarm",
        alpha=0.55,
        s=18,
    )
    limits = [
        min(predictions["observed_tmax_c"].min(), predictions["predicted_tmax_c"].min()),
        max(predictions["observed_tmax_c"].max(), predictions["predicted_tmax_c"].max()),
    ]
    ax.plot(limits, limits, color="black", linestyle="--", linewidth=1)
    ax.set(
        title=f"Holdout accuracy (MAE {metrics['temperature_mae_c']:.2f}°C)",
        xlabel="Observed (°C)",
        ylabel="Predicted (°C)",
    )

    ax = axes[1, 1]
    truth = predictions["observed_hot_day"].to_numpy()
    predicted = predictions["predicted_hot_day"].to_numpy()
    matrix = np.array(
        [
            [np.sum((truth == 0) & (predicted == 0)), np.sum((truth == 0) & (predicted == 1))],
            [np.sum((truth == 1) & (predicted == 0)), np.sum((truth == 1) & (predicted == 1))],
        ]
    )
    ax.imshow(matrix, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=16)
    ax.set_xticks([0, 1], ["Normal", "Hot"])
    ax.set_yticks([0, 1], ["Normal", "Hot"])
    ax.set(
        title=f"Hot-day detection (recall {metrics['hot_day_recall']:.1%})",
        xlabel="Predicted",
        ylabel="Observed",
    )

    fig.text(
        0.01,
        0.01,
        "Source: Deutscher Wetterdienst Climate Data Center, station 00917 Darmstadt. "
        "Research model—not an official warning service.",
        fontsize=9,
        color="#444444",
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)
