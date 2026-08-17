import unittest

import numpy as np
import pandas as pd

from heatrisk.features import build_supervised, split_time


class FeatureTests(unittest.TestCase):
    def setUp(self):
        index = pd.date_range("2022-11-01", periods=900, freq="D")
        values = np.arange(len(index), dtype=float)
        self.daily = pd.DataFrame(
            {
                "TXK": 15 + values / 100,
                "TNK": 5 + values / 200,
                "TMK": 10 + values / 150,
                "UPM": 70 + np.sin(values),
                "RSK": values % 3,
                "SDK": values % 10,
                "VPM": 8 + values / 1000,
            },
            index=index,
        )

    def test_target_is_next_day(self):
        supervised = build_supervised(self.daily)
        first = supervised.iloc[0]
        feature_date = supervised.index[0]
        self.assertEqual(first["target_date"], feature_date + pd.Timedelta(days=1))
        self.assertEqual(first["target_tmax"], self.daily.loc[feature_date + pd.Timedelta(days=1), "TXK"])

    def test_inference_row_targets_day_after_latest_observation(self):
        inference = build_supervised(self.daily, drop_unlabeled=False).iloc[-1]
        self.assertEqual(inference["target_date"], self.daily.index.max() + pd.Timedelta(days=1))
        self.assertTrue(pd.isna(inference["target_tmax"]))

    def test_split_is_strictly_chronological(self):
        supervised = build_supervised(self.daily)
        train, validation, test = split_time(supervised, "2022-12-31", "2023-12-31")
        self.assertLessEqual(train["target_date"].max(), pd.Timestamp("2022-12-31"))
        self.assertGreater(validation["target_date"].min(), pd.Timestamp("2022-12-31"))
        self.assertGreater(test["target_date"].min(), pd.Timestamp("2023-12-31"))


if __name__ == "__main__":
    unittest.main()
