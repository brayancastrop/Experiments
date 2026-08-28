"""End-to-end demo of the wheel engine against a mock broker.

Run from the repository root::

    python -m options.examples.run_scan

It seeds a :class:`MockBroker` with two symbols - one in a high-IV regime that
passes the gate, one in a calm regime that does not - runs the deterministic
scanner (Layer 2), then the advisory analyst (Layer 3). No orders are placed;
the point is to see *proposals* and the analyst's read on them.
"""

from __future__ import annotations

from options.analyst import RuleBasedAnalyst
from options.broker import MockBroker
from options.config import WheelConfig
from options.models import AccountState, OptionQuote, OptionRight, SymbolMarketData
from options.scanner import scan


def _put(symbol, strike, delta, bid, ask, underlying, dte=30, oi=800):
    return OptionQuote(
        symbol=symbol,
        right=OptionRight.PUT,
        strike=strike,
        expiry="2025-02-21",
        dte=dte,
        bid=bid,
        ask=ask,
        delta=delta,
        open_interest=oi,
        underlying_price=underlying,
    )


def build_broker() -> MockBroker:
    # A rising IV series; "now" = 0.42 sits high in its own range (IV Rank ~80).
    rich_iv_history = [0.15, 0.18, 0.22, 0.30, 0.45]
    calm_iv_history = [0.15, 0.18, 0.22, 0.30, 0.45]

    # Underlying priced so a single cash-secured put (~$2,800 collateral) fits
    # inside the 5% concentration cap of this $60k account (= $3,000/position).
    hot = SymbolMarketData(
        symbol="HOT",
        underlying_price=30.0,
        current_iv=0.42,  # high in range -> gate opens (IV Rank ~90)
        iv_history=rich_iv_history,
        put_chain=[
            _put("HOT", 28, -0.28, 0.45, 0.55, underlying=30.0),
            _put("HOT", 27, -0.18, 0.20, 0.30, underlying=30.0),
        ],
    )
    calm = SymbolMarketData(
        symbol="CALM",
        underlying_price=50.0,
        current_iv=0.16,  # low in range -> gate stays shut (IV Rank ~3)
        iv_history=calm_iv_history,
        put_chain=[
            _put("CALM", 48, -0.25, 0.6, 0.8, underlying=50.0),
        ],
    )

    account = AccountState(net_liquidation=60_000.0, buying_power=40_000.0)
    return MockBroker(account=account, data={"HOT": hot, "CALM": calm})


def main() -> None:
    broker = build_broker()
    config = WheelConfig()  # defaults: IV Rank gate 50, delta 0.30, 30-45 DTE

    candidates = scan(broker.universe(), broker.account_state(), config)

    print("=== Layer 2: scanner proposals (deterministic) ===")
    if not candidates:
        print("  (no candidates - nothing passed the gate/filters)")
    for c in candidates:
        print(f"  - {c.rationale}")

    print("\n=== Layer 3: analyst review (advisory, read-only) ===")
    analyst = RuleBasedAnalyst()
    for review in analyst.review_all(candidates):
        verdict = "APPROVE" if review.approved else "VETO"
        print(f"  [{verdict}] {review.candidate.symbol}: {review.notes}")

    print(
        "\nNote: CALM is filtered out at the IV-Rank gate; no order is ever "
        "placed here - execution stays behind human confirmation."
    )


if __name__ == "__main__":
    main()
