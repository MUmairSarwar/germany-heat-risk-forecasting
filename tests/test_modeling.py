import unittest

import numpy as np

from heatrisk.modeling import _conformal_radius


class ModelingTests(unittest.TestCase):
    def test_conformal_radius_is_nonnegative_and_conservative(self):
        residuals = np.array([-1.0, 0.2, 0.5, 2.0, -0.7])
        radius = _conformal_radius(residuals, 0.8)
        self.assertGreaterEqual(radius, 0)
        self.assertGreaterEqual(np.mean(np.abs(residuals) <= radius), 0.8)

    def test_invalid_coverage_fails(self):
        with self.assertRaises(ValueError):
            _conformal_radius(np.array([1.0]), 1.0)


if __name__ == "__main__":
    unittest.main()

