"""Contract selection (Layer 1) - the wheel's ``find_eligible_contracts``.

The flow mirrors the reference bots (thetagang, alpaca options-wheel) but adds
the **IV-Rank gate first**, before any delta/price work:

1. **IV-Rank gate.** If IV Rank is below the threshold, return nothing - the
   whole point of the strategy is to only sell premium when it is rich.
2. **Strike filter.** Puts: keep strikes at or below ``price * (1 + buffer)``
   (excludes deep-ITM puts). Calls: keep OTM strikes at or above the price.
3. **DTE filter.** Keep expirations within ``[min_dte, max_dte]``.
4. **Ordered quality filters.** Minimum premium, then ``|delta| <= target``,
   then minimum open interest.
5. **Pick the richest acceptable contract**: highest ``|delta|`` still within
   the delta budget (richest premium within the risk cap), tie-broken by
   premium, then by DTE closest to target.

Sizing and the hard cash/limit checks come from :mod:`options.sizing`, so a
returned :class:`Candidate` is already affordable and within risk limits.
"""

from __future__ import annotations

from typing import Iterable, Optional

from .config import WheelConfig
from .iv_rank import iv_rank
from .models import Action, AccountState, Candidate, OptionQuote, OptionRight, SymbolMarketData
from .sizing import (
    contracts_for_covered_call,
    contracts_for_csp,
    csp_collateral,
)

__all__ = ["select_put", "select_call"]


def _annualized(premium: float, basis: float, dte: int) -> float:
    """Premium as a fraction of ``basis``, annualized by days to expiration."""
    if basis <= 0 or dte <= 0:
        return 0.0
    return (premium / basis) * (365.0 / dte)


def _rank_key(quote: OptionQuote, target_delta: int, target_dte: int):
    # Richest premium within the risk budget = highest |delta| still <= target;
    # then higher premium; then DTE closest to the target.
    return (
        abs(quote.delta),
        quote.mid,
        -abs(quote.dte - target_dte),
    )


def _best(
    quotes: Iterable[OptionQuote],
    resolved,
) -> Optional[OptionQuote]:
    eligible = [
        q
        for q in quotes
        if q.mid >= resolved.min_premium
        and abs(q.delta) <= resolved.target_delta
        and q.open_interest >= resolved.min_open_interest
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda q: _rank_key(q, resolved.target_delta, resolved.target_dte))


def select_put(
    data: SymbolMarketData,
    account: AccountState,
    config: WheelConfig,
) -> Optional[Candidate]:
    """Best cash-secured put for ``data``, or ``None`` if nothing qualifies."""
    resolved = config.for_symbol(data.symbol)

    rank = iv_rank(data.current_iv, data.iv_history, resolved.iv_lookback_days)
    # 1e-9 tolerance: an IV Rank exactly on the threshold opens the gate even
    # when floating-point error nudges it a hair below (see passes_iv_gate).
    if rank < resolved.iv_rank_threshold - 1e-9:
        return None

    max_strike = data.underlying_price * (1.0 + resolved.strike_buffer_pct)
    universe = [
        q
        for q in data.put_chain
        if q.right is OptionRight.PUT
        and q.strike <= max_strike
        and resolved.min_dte <= q.dte <= resolved.max_dte
    ]
    chosen = _best(universe, resolved)
    if chosen is None:
        return None

    contracts = contracts_for_csp(account, chosen, config)
    if contracts <= 0:
        return None

    collateral = csp_collateral(chosen.strike, contracts)
    premium = round(chosen.mid * 100.0 * contracts, 2)
    annualized = _annualized(premium, collateral, chosen.dte)

    return Candidate(
        symbol=data.symbol,
        action=Action.SELL_PUT,
        quote=chosen,
        contracts=contracts,
        collateral=collateral,
        premium=premium,
        iv_rank=round(rank, 1),
        annualized_return=round(annualized, 4),
        rationale=(
            f"IV Rank {rank:.0f} >= {resolved.iv_rank_threshold:.0f}; sell "
            f"{contracts}x {data.symbol} {chosen.strike}P {chosen.dte}DTE "
            f"|delta|={abs(chosen.delta):.2f} for ${premium:.0f} "
            f"(~{annualized*100:.1f}% annualized on ${collateral:.0f})"
        ),
    )


def select_call(
    data: SymbolMarketData,
    account: AccountState,
    config: WheelConfig,
) -> Optional[Candidate]:
    """Best covered call for ``data``, or ``None`` if nothing qualifies.

    Requires at least 100 owned shares of the symbol (see
    :func:`options.sizing.contracts_for_covered_call`).
    """
    resolved = config.for_symbol(data.symbol)

    rank = iv_rank(data.current_iv, data.iv_history, resolved.iv_lookback_days)
    # 1e-9 tolerance: an IV Rank exactly on the threshold opens the gate even
    # when floating-point error nudges it a hair below (see passes_iv_gate).
    if rank < resolved.iv_rank_threshold - 1e-9:
        return None

    # Covered calls are sold out-of-the-money (strike above the current price).
    universe = [
        q
        for q in data.call_chain
        if q.right is OptionRight.CALL
        and q.strike >= data.underlying_price
        and resolved.min_dte <= q.dte <= resolved.max_dte
    ]
    chosen = _best(universe, resolved)
    if chosen is None:
        return None

    contracts = contracts_for_covered_call(account, chosen, config)
    if contracts <= 0:
        return None

    premium = round(chosen.mid * 100.0 * contracts, 2)
    share_notional = data.underlying_price * 100.0 * contracts
    annualized = _annualized(premium, share_notional, chosen.dte)

    return Candidate(
        symbol=data.symbol,
        action=Action.SELL_CALL,
        quote=chosen,
        contracts=contracts,
        collateral=0.0,  # shares already owned; no new cash tied up
        premium=premium,
        iv_rank=round(rank, 1),
        annualized_return=round(annualized, 4),
        rationale=(
            f"IV Rank {rank:.0f} >= {resolved.iv_rank_threshold:.0f}; sell "
            f"{contracts}x {data.symbol} {chosen.strike}C {chosen.dte}DTE "
            f"covered, |delta|={abs(chosen.delta):.2f} for ${premium:.0f} "
            f"(~{annualized*100:.1f}% annualized on shares)"
        ),
    )
