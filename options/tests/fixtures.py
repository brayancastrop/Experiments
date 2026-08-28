"""Shared builders for the test suite."""

from __future__ import annotations

from options.models import AccountState, OptionQuote, OptionRight, SymbolMarketData

# A rising IV series: current 0.40 sits at IV Rank 75 (well above the 50 gate).
HIGH_IV_HISTORY = [0.10, 0.20, 0.30, 0.40, 0.50]
HIGH_IV_NOW = 0.40  # rank = (0.40 - 0.10) / (0.50 - 0.10) * 100 = 75
LOW_IV_NOW = 0.12  # rank = 5, below the gate


def put(symbol, strike, delta, bid, ask, dte=30, oi=500, underlying=100.0):
    return OptionQuote(
        symbol=symbol,
        right=OptionRight.PUT,
        strike=strike,
        expiry="2025-01-17",
        dte=dte,
        bid=bid,
        ask=ask,
        delta=delta,  # puts are negative
        open_interest=oi,
        underlying_price=underlying,
    )


def call(symbol, strike, delta, bid, ask, dte=30, oi=500, underlying=100.0):
    return OptionQuote(
        symbol=symbol,
        right=OptionRight.CALL,
        strike=strike,
        expiry="2025-01-17",
        dte=dte,
        bid=bid,
        ask=ask,
        delta=delta,
        open_interest=oi,
        underlying_price=underlying,
    )


def market_data(symbol="ACME", underlying=100.0, current_iv=HIGH_IV_NOW, puts=(), calls=()):
    return SymbolMarketData(
        symbol=symbol,
        underlying_price=underlying,
        current_iv=current_iv,
        iv_history=HIGH_IV_HISTORY,
        put_chain=puts,
        call_chain=calls,
    )


def account(net_liq=200_000.0, buying_power=50_000.0, shares=None):
    return AccountState(
        net_liquidation=net_liq,
        buying_power=buying_power,
        shares_owned=shares or {},
    )
