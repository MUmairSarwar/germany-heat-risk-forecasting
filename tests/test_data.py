import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd

from heatrisk.data import clean_daily, load_dwd_daily
from heatrisk.evaluation import annual_hot_days


class DataTests(unittest.TestCase):
    def test_recent_archive_refreshes_while_named_history_is_cached(self):
        def archive(day):
            buffer = BytesIO()
            with ZipFile(buffer, "w") as zipped:
                zipped.writestr(
                    "produkt_klima_tag_test.txt",
                    "MESS_DATUM;RSK;SDK;VPM;TMK;UPM;TXK;TNK\n"
                    f"{day};0;1;2;3;4;5;6\n",
                )
            return buffer.getvalue()

        historical_url = "https://example.com/tageswerte_KL_00917_20230101_20231231_hist.zip"
        with TemporaryDirectory() as cache:
            with patch("heatrisk.data.discover_historical_url", return_value=historical_url):
                with patch("heatrisk.data._read_url", side_effect=[
                    archive(20231231), archive(20240101), archive(20240102)
                ]) as read_url:
                    first = load_dwd_daily(cache_dir=cache)
                    second = load_dwd_daily(cache_dir=cache)

        self.assertEqual(first.index.max(), pd.Timestamp("2024-01-01"))
        self.assertEqual(second.index.max(), pd.Timestamp("2024-01-02"))
        self.assertEqual(read_url.call_count, 3)
        self.assertEqual(read_url.call_args_list[0].args, (historical_url,))

    def test_clean_daily_replaces_sentinel_and_deduplicates(self):
        frame = pd.DataFrame(
            {
                "MESS_DATUM": [20240101, 20240101, 20240102],
                "RSK": [0.0, 1.0, -999],
                "SDK": [1.0, 2.0, 3.0],
                "VPM": [8.0, 9.0, 10.0],
                "TMK": [5.0, 6.0, 7.0],
                "UPM": [70.0, 71.0, 72.0],
                "TXK": [8.0, 9.0, 10.0],
                "TNK": [2.0, 3.0, 4.0],
            }
        )
        result = clean_daily(frame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.loc["2024-01-01", "TXK"], 9.0)
        self.assertTrue(pd.isna(result.loc["2024-01-02", "RSK"]))

    def test_annual_hot_days_excludes_partial_years(self):
        full = pd.date_range("2024-01-01", "2024-12-31", freq="D")
        partial = pd.date_range("2025-01-01", periods=100, freq="D")
        frame = pd.DataFrame({"TXK": 31.0}, index=full.append(partial))
        result = annual_hot_days(frame)
        self.assertEqual(result["year"].tolist(), [2024])
        self.assertEqual(result["hot_days"].tolist(), [366])


if __name__ == "__main__":
    unittest.main()
