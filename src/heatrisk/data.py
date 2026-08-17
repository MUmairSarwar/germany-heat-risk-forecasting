"""Download and clean DWD Climate Data Center daily observations."""

from __future__ import annotations

import io
import re
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

BASE = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl"
REQUIRED_COLUMNS = ["MESS_DATUM", "RSK", "SDK", "VPM", "TMK", "UPM", "TXK", "TNK"]


def _read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "rhine-main-heat-risk/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def discover_historical_url(station_id: int) -> str:
    """Return the current historical archive URL for a DWD station."""
    listing = _read_url(f"{BASE}/historical/").decode("utf-8", errors="ignore")
    pattern = rf'tageswerte_KL_{station_id:05d}_\d{{8}}_\d{{8}}_hist\.zip'
    matches = sorted(set(re.findall(pattern, listing)))
    if not matches:
        raise FileNotFoundError(f"No DWD historical archive found for station {station_id}")
    return f"{BASE}/historical/{matches[-1]}"


def recent_url(station_id: int) -> str:
    return f"{BASE}/recent/tageswerte_KL_{station_id:05d}_akt.zip"


def _parse_archive(raw_zip: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        names = [name for name in archive.namelist() if name.startswith("produkt_klima_tag_")]
        if len(names) != 1:
            raise ValueError("Expected one daily climate data file in DWD archive")
        with archive.open(names[0]) as data_file:
            frame = pd.read_csv(data_file, sep=";", skipinitialspace=True)
    frame.columns = [column.strip() for column in frame.columns]
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"DWD archive is missing columns: {missing}")
    return frame[REQUIRED_COLUMNS].copy()


def clean_daily(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply documented DWD missing-value rules and normalize the daily index."""
    result = frame.copy()
    result["date"] = pd.to_datetime(result.pop("MESS_DATUM").astype(str), format="%Y%m%d")
    for column in result.columns:
        if column != "date":
            result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.replace(-999, float("nan"))
    result = result.drop_duplicates("date", keep="last").sort_values("date")
    result = result.set_index("date")
    result.index.name = "date"
    return result


def load_dwd_daily(station_id: int = 917, cache_dir: Path | str = ".cache/dwd") -> pd.DataFrame:
    """Download/cache, merge, and clean historical plus recent DWD observations."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    sources = {
        "historical": discover_historical_url(station_id),
        "recent": recent_url(station_id),
    }
    frames: list[pd.DataFrame] = []
    for label, url in sources.items():
        destination = cache / f"station_{station_id:05d}_{label}.zip"
        if not destination.exists():
            destination.write_bytes(_read_url(url))
        frames.append(_parse_archive(destination.read_bytes()))
    return clean_daily(pd.concat(frames, ignore_index=True))


def save_processed(frame: pd.DataFrame, path: Path | str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, date_format="%Y-%m-%d")

