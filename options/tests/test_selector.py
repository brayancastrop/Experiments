import unittest

from options.config import WheelConfig
from options.models import Action
from options.selector import select_call, select_put

from .fixtures import LOW_IV_NOW, account, call, market_data, put


class SelectPutTests(unittest.TestCase):
    def setUp(self):
        self.cfg = WheelConfig()
        self.acct = account(net_liq=200_000, buying_power=50_000)

    def test_picks_richest_within_delta_budget(self):
        data = market_data(
            puts=[
                put("ACME", strike=95, delta=-0.30, bid=1.0, ask=1.2),  # eligible
                put("ACME", strike=90, delta=-0.20, bid=0.5, ask=0.6),  # eligible, thinner
                put("ACME", strike=97, delta=-0.40, bid=2.0, ask=2.2),  # delta too high
            ]
        )
        cand = select_put(data, self.acct, self.cfg)
        self.assertIsNotNone(cand)
        self.assertEqual(cand.action, Action.SELL_PUT)
        self.assertEqual(cand.quote.strike, 95)  # |delta| 0.30 beats 0.20
        self.assertEqual(cand.contracts, 1)
        self.assertAlmostEqual(cand.premium, 110.0)  # mid 1.1 * 100
        self.assertEqual(cand.iv_rank, 75.0)
        self.assertGreater(cand.annualized_return, 0)

    def test_iv_gate_blocks_low_vol(self):
        data = market_data(
            current_iv=LOW_IV_NOW,
            puts=[put("ACME", strike=95, delta=-0.30, bid=1.0, ask=1.2)],
        )
        from options.selector import select_put

        self.assertIsNone(select_put(data, self.acct, self.cfg))

    def test_open_interest_floor_excludes(self):
        data = market_data(
            puts=[put("ACME", strike=95, delta=-0.30, bid=1.0, ask=1.2, oi=10)]
        )
        from options.selector import select_put

        self.assertIsNone(select_put(data, self.acct, self.cfg))

    def test_dte_window_excludes(self):
        data = market_data(
            puts=[put("ACME", strike=95, delta=-0.30, bid=1.0, ask=1.2, dte=7)]
        )
        from options.selector import select_put

        self.assertIsNone(select_put(data, self.acct, self.cfg))

    def test_deep_itm_strike_excluded_by_buffer(self):
        # strike 110 on a $100 underlying is above price*(1+5%) = 105.
        data = market_data(
            puts=[put("ACME", strike=110, delta=-0.30, bid=1.0, ask=1.2)]
        )
        from options.selector import select_put

        self.assertIsNone(select_put(data, self.acct, self.cfg))


class SelectCallTests(unittest.TestCase):
    def setUp(self):
        self.cfg = WheelConfig()

    def test_covered_call_requires_shares(self):
        from options.selector import select_call

        data = market_data(calls=[call("ACME", strike=105, delta=0.25, bid=1.4, ask=1.6)])
        self.assertIsNone(select_call(data, account(shares={}), self.cfg))

        cand = select_call(data, account(shares={"ACME": 100}), self.cfg)
        self.assertIsNotNone(cand)
        self.assertEqual(cand.action, Action.SELL_CALL)
        self.assertEqual(cand.collateral, 0.0)
        self.assertAlmostEqual(cand.premium, 150.0)  # mid 1.5 * 100

    def test_itm_call_excluded(self):
        from options.selector import select_call

        data = market_data(calls=[call("ACME", strike=95, delta=0.25, bid=1.4, ask=1.6)])
        self.assertIsNone(select_call(data, account(shares={"ACME": 100}), self.cfg))


if __name__ == "__main__":
    unittest.main()
