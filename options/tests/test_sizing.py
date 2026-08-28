import unittest

from options.config import WheelConfig
from options.sizing import (
    can_afford_csp,
    contracts_for_covered_call,
    contracts_for_csp,
    csp_collateral,
    max_position_pct,
    max_position_value,
    shares_backing_calls,
)

from .fixtures import account, call, put


class TierTests(unittest.TestCase):
    def setUp(self):
        self.cfg = WheelConfig()

    def test_small_account_concentrates(self):
        self.assertEqual(max_position_pct(10_000, self.cfg.sizing_tiers), 0.20)

    def test_large_account_diversifies(self):
        self.assertEqual(max_position_pct(30_000, self.cfg.sizing_tiers), 0.05)

    def test_boundary_is_inclusive(self):
        self.assertEqual(max_position_pct(25_000, self.cfg.sizing_tiers), 0.05)


class CollateralTests(unittest.TestCase):
    def test_collateral_is_strike_times_100(self):
        self.assertEqual(csp_collateral(50, 1), 5_000)
        self.assertEqual(csp_collateral(50, 2), 10_000)


class AffordabilityTests(unittest.TestCase):
    def setUp(self):
        self.cfg = WheelConfig()

    def test_position_cap_blocks_oversized_put(self):
        # 5% of 30k = 1500 cap; a 50-strike put needs 5000 collateral.
        acct = account(net_liq=30_000, buying_power=30_000)
        q = put("ACME", strike=50, delta=-0.3, bid=1.0, ask=1.2)
        self.assertFalse(can_afford_csp(acct, q, self.cfg))

    def test_no_margin_blocks_when_cash_short(self):
        # 20% of 10k = 2000 cap allows it, but only $1000 cash is available.
        acct = account(net_liq=10_000, buying_power=1_000)
        q = put("ACME", strike=15, delta=-0.3, bid=0.5, ask=0.6)
        self.assertFalse(can_afford_csp(acct, q, self.cfg))

    def test_affordable_within_all_limits(self):
        acct = account(net_liq=10_000, buying_power=10_000)
        q = put("ACME", strike=15, delta=-0.3, bid=0.5, ask=0.6)
        self.assertTrue(can_afford_csp(acct, q, self.cfg))
        self.assertEqual(contracts_for_csp(acct, q, self.cfg), 1)

    def test_unaffordable_returns_zero_contracts(self):
        acct = account(net_liq=10_000, buying_power=1_000)
        q = put("ACME", strike=15, delta=-0.3, bid=0.5, ask=0.6)
        self.assertEqual(contracts_for_csp(acct, q, self.cfg), 0)

    def test_margin_allowed_bypasses_cash_check(self):
        cfg = WheelConfig(allow_margin=True)
        acct = account(net_liq=100_000, buying_power=100)  # tiny cash
        q = put("ACME", strike=15, delta=-0.3, bid=0.5, ask=0.6)
        self.assertTrue(can_afford_csp(acct, q, cfg))


class CoveredCallTests(unittest.TestCase):
    def setUp(self):
        self.cfg = WheelConfig()

    def test_shares_back_one_contract_per_hundred(self):
        acct = account(shares={"ACME": 250})
        self.assertEqual(shares_backing_calls(acct, "ACME"), 2)

    def test_capped_at_max_per_symbol(self):
        acct = account(shares={"ACME": 250})
        q = call("ACME", strike=105, delta=0.25, bid=1.4, ask=1.6)
        # backed by 2, but max_contracts_per_symbol defaults to 1.
        self.assertEqual(contracts_for_covered_call(acct, q, self.cfg), 1)

    def test_no_shares_no_call(self):
        acct = account(shares={})
        q = call("ACME", strike=105, delta=0.25, bid=1.4, ask=1.6)
        self.assertEqual(contracts_for_covered_call(acct, q, self.cfg), 0)


if __name__ == "__main__":
    unittest.main()
