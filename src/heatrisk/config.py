from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    station_id: int = 917
    station_name: str = "Darmstadt"
    hot_day_threshold_c: float = 30.0
    train_end: str = "2022-12-31"
    validation_end: str = "2024-12-31"
    interval_coverage: float = 0.80
    random_seed: int = 42
    cache_dir: Path = Path(".cache/dwd")
    output_dir: Path = Path("outputs")
    model_dir: Path = Path("models")


CONFIG = ProjectConfig()

