"""Layer 2 - scan a universe into a ranked list of candidates.

For each symbol the scanner asks Layer 1 for the best put (and, when shares are
owned, the best covered call), then ranks all survivors by annualized return
and applies the run-wide ``max_new_contracts_per_run`` budget.

The scanner *proposes*; it never places orders. It is fully deterministic.
"""

from __future__ import annotations

from typing import Iterable

from .config import WheelConfig
from .models import AccountState, Candidate, SymbolMarketData
from .selector import select_call, select_put

__all__ = ["scan"]


def scan(
    universe: Iterable[SymbolMarketData],
    account: AccountState,
    config: WheelConfig,
) -> list[Candidate]:
    """Return proposed trades, richest annualized yield first.

    A symbol may contribute a put and/or a covered call. The combined list is
    sorted by annualized return and truncated to ``max_new_contracts_per_run``.
    """
    candidates: list[Candidate] = []

    for data in universe:
        put = select_put(data, account, config)
        if put is not None:
            candidates.append(put)

        # Only bother with covered calls when the account actually holds shares.
        if account.shares_owned.get(data.symbol, 0) >= 100:
            call = select_call(data, account, config)
            if call is not None:
                candidates.append(call)

    candidates.sort(key=lambda c: c.annualized_return, reverse=True)
    return candidates[: config.max_new_contracts_per_run]
