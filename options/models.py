"""Plain data structures shared across the engine.

Deliberately broker-agnostic: an IBKR adapter (or the test :class:`MockBroker`)
is responsible for turning raw market data into these objects, so the
deterministic core never depends on any broker SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

__all__ = [
    "OptionRight",
    "Action",
    "OptionQuote",
    "AccountState",
    "SymbolMarketData",
    "Candidate",
]


class OptionRight(str, Enum):
    PUT = "P"
    CALL = "C"


class Action(str, Enum):
    """The wheel only ever *sells* options to collect premium."""

    SELL_PUT = "SELL_PUT"  # cash-secured put
    SELL_CALL = "SELL_CALL"  # covered call


@dataclass(frozen=True)
class OptionQuote:
    """A single option contract quote.

    ``delta`` is signed (puts negative, calls positive), as brokers report it.
    ``expiry`` is an ISO ``YYYY-MM-DD`` string; ``dte`` is days to expiration.
    """

    symbol: str
    right: OptionRight
    strike: float
    expiry: str
    dte: int
    bid: float
    ask: float
    delta: float
    open_interest: int
    underlying_price: float

    @property
    def mid(self) -> float:
        """Midpoint premium per share (multiply by 100 for per-contract $)."""
        return round((self.bid + self.ask) / 2.0, 4)


@dataclass(frozen=True)
class AccountState:
    """A snapshot of the account, cash-secured (no margin assumed).

    ``buying_power`` is cash actually available to secure puts. ``shares_owned``
    maps a symbol to the number of shares held, which caps covered calls at one
    contract per 100 shares.
    """

    net_liquidation: float
    buying_power: float
    shares_owned: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class SymbolMarketData:
    """Everything the scanner needs about one symbol for a single run."""

    symbol: str
    underlying_price: float
    current_iv: float
    iv_history: Sequence[float]
    put_chain: Sequence[OptionQuote] = ()
    call_chain: Sequence[OptionQuote] = ()


@dataclass(frozen=True)
class Candidate:
    """A proposed (never auto-executed) trade with its supporting numbers."""

    symbol: str
    action: Action
    quote: OptionQuote
    contracts: int
    collateral: float  # cash tied up (CSP) or 0 for covered calls
    premium: float  # total credit received, dollars
    iv_rank: float
    annualized_return: float  # premium / collateral, annualized by DTE
    rationale: str = ""

    @property
    def premium_per_contract(self) -> float:
        return round(self.quote.mid * 100.0, 2)
