import unittest

from options.config import WheelConfig
from options.models import Action
from options.scanner import scan

from .fixtures import LOW_IV_NOW, account, market_data, put


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.cfg = WheelConfig()
        self.acct = account(net_liq=200_000, buying_power=100_000)

    def test_only_symbols_passing_the_gate_appear(self):
        universe = [
            market_data(symbol="HOT", puts=[put("HOT", 95, -0.30, 1.0, 1.2)]),
            market_data(
                symbol="COLD",
                current_iv=LOW_IV_NOW,
                puts=[put("COLD", 95, -0.30, 1.0, 1.2)],
            ),
        ]
        out = scan(universe, self.acct, self.cfg)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].symbol, "HOT")

    def test_ranked_by_annualized_return_and_capped(self):
        cfg = WheelConfig(max_new_contracts_per_run=2)
        # Same collateral basis; higher premium -> higher annualized return.
        universe = [
            market_data(symbol="A", puts=[put("A", 95, -0.30, 0.4, 0.6)]),  # mid .5
            market_data(symbol="B", puts=[put("B", 95, -0.30, 1.9, 2.1)]),  # mid 2.0
            market_data(symbol="C", puts=[put("C", 95, -0.30, 0.9, 1.1)]),  # mid 1.0
        ]
        out = scan(universe, self.acct, cfg)
        self.assertEqual(len(out), 2)  # truncated to the run budget
        self.assertEqual([c.symbol for c in out], ["B", "C"])  # richest first

    def test_covered_call_included_when_shares_held(self):
        acct = account(net_liq=200_000, buying_power=100_000, shares={"ACME": 100})
        from .fixtures import call

        universe = [
            market_data(
                symbol="ACME",
                puts=[put("ACME", 95, -0.30, 1.0, 1.2)],
                calls=[call("ACME", 105, 0.25, 1.4, 1.6)],
            )
        ]
        out = scan(universe, acct, WheelConfig(max_new_contracts_per_run=5))
        actions = {c.action for c in out}
        self.assertIn(Action.SELL_PUT, actions)
        self.assertIn(Action.SELL_CALL, actions)


if __name__ == "__main__":
    unittest.main()
