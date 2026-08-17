import unittest

import pandas as pd

from heatrisk.data import clean_daily
from heatrisk.evaluation import annual_hot_days


class DataTests(unittest.TestCase):
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
