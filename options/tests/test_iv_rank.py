import unittest

from options.iv_rank import (
    InsufficientDataError,
    iv_percentile,
    iv_rank,
    passes_iv_gate,
    realized_volatility,
)


class IVRankTests(unittest.TestCase):
    HIST = [0.10, 0.20, 0.30, 0.40, 0.50]

    def test_min_max_and_midpoint(self):
        self.assertAlmostEqual(iv_rank(0.10, self.HIST), 0.0)
        self.assertAlmostEqual(iv_rank(0.50, self.HIST), 100.0)
        self.assertAlmostEqual(iv_rank(0.30, self.HIST), 50.0)

    def test_clamped_to_bounds(self):
        self.assertEqual(iv_rank(0.90, self.HIST), 100.0)
        self.assertEqual(iv_rank(0.01, self.HIST), 0.0)

    def test_flat_history_is_neutral_low(self):
        self.assertEqual(iv_rank(0.20, [0.20, 0.20, 0.20]), 0.0)

    def test_lookback_truncates_window(self):
        # Only the last 2 observations -> range [0.40, 0.50]; 0.45 -> 50.
        self.assertAlmostEqual(iv_rank(0.45, self.HIST, lookback=2), 50.0)

    def test_too_short_history_raises(self):
        with self.assertRaises(InsufficientDataError):
            iv_rank(0.3, [0.3])

    def test_negative_or_nan_rejected(self):
        with self.assertRaises(ValueError):
            iv_rank(0.3, [0.1, -0.2, 0.3])


class IVPercentileTests(unittest.TestCase):
    def test_share_below(self):
        self.assertAlmostEqual(iv_percentile(0.35, [0.1, 0.2, 0.3, 0.4]), 75.0)

    def test_all_below(self):
        self.assertAlmostEqual(iv_percentile(1.0, [0.1, 0.2, 0.3]), 100.0)


class GateTests(unittest.TestCase):
    HIST = [0.10, 0.20, 0.30, 0.40, 0.50]

    def test_gate_open_at_threshold(self):
        # rank(0.30) == 50 -> at threshold 50 is open.
        self.assertTrue(passes_iv_gate(0.30, self.HIST, threshold=50))

    def test_gate_closed_below_threshold(self):
        self.assertFalse(passes_iv_gate(0.30, self.HIST, threshold=60))

    def test_gate_fails_closed_on_thin_data(self):
        self.assertFalse(passes_iv_gate(0.3, [0.3], threshold=50))


class RealizedVolTests(unittest.TestCase):
    def test_constant_prices_zero_vol(self):
        self.assertEqual(realized_volatility([100.0, 100.0, 100.0]), 0.0)

    def test_varying_prices_positive_vol(self):
        self.assertGreater(realized_volatility([100, 101, 99, 102, 98]), 0.0)

    def test_requires_two_prices(self):
        with self.assertRaises(InsufficientDataError):
            realized_volatility([100.0])

    def test_rejects_nonpositive_prices(self):
        with self.assertRaises(ValueError):
            realized_volatility([100.0, 0.0])


if __name__ == "__main__":
    unittest.main()
