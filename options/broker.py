"""Broker boundary - an interface plus an in-memory mock.

The deterministic core never imports a broker SDK. Instead it talks to this
:class:`BrokerClient` protocol. A real implementation would wrap ``ib_async``
for Interactive Brokers (the DRY win: connection, market data and order
plumbing are already solved by that library, and studied from thetagang as a
reference).

**Execution is deliberately fenced off.** ``place_order`` exists on the
protocol, but:

* the scanner/selector never call it - they only return proposals;
* :class:`MockBroker.place_order` merely records intent and refuses unless the
  order is explicitly flagged as human-confirmed.

That keeps the "an LLM/agent must never pull the trigger" rule structural, not
just a comment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence, runtime_checkable

from .models import AccountState, Candidate, OptionQuote, SymbolMarketData

__all__ = ["BrokerClient", "OrderTicket", "MockBroker", "ExecutionBlocked"]


class ExecutionBlocked(RuntimeError):
    """Raised when an order reaches the broker without human confirmation."""


@dataclass(frozen=True)
class OrderTicket:
    """A concrete order derived from a :class:`Candidate`.

    ``human_confirmed`` must be set by a person (or an out-of-band, non-LLM
    workflow). The broker refuses to act otherwise.
    """

    candidate: Candidate
    limit_price: float
    human_confirmed: bool = False


@runtime_checkable
class BrokerClient(Protocol):
    """Everything the engine needs from a broker - read paths, plus a guarded
    write path that stays out of the automated loop."""

    def account_state(self) -> AccountState: ...

    def market_data(self, symbol: str, iv_lookback: int) -> SymbolMarketData: ...

    def option_chain(self, symbol: str) -> Sequence[OptionQuote]: ...

    def place_order(self, ticket: OrderTicket) -> str:
        """Submit an order. Implementations MUST reject tickets that are not
        ``human_confirmed`` by raising :class:`ExecutionBlocked`."""
        ...


@dataclass
class MockBroker:
    """In-memory broker for tests, examples and paper analysis.

    Seed it with an :class:`AccountState` and per-symbol
    :class:`SymbolMarketData`; it serves those back and records any (confirmed)
    orders in :attr:`submitted` without touching a real market.
    """

    account: AccountState
    data: dict[str, SymbolMarketData] = field(default_factory=dict)
    submitted: list[OrderTicket] = field(default_factory=list)

    def account_state(self) -> AccountState:
        return self.account

    def market_data(self, symbol: str, iv_lookback: int = 252) -> SymbolMarketData:
        return self.data[symbol]

    def option_chain(self, symbol: str) -> Sequence[OptionQuote]:
        md = self.data[symbol]
        return list(md.put_chain) + list(md.call_chain)

    def universe(self) -> list[SymbolMarketData]:
        return list(self.data.values())

    def place_order(self, ticket: OrderTicket) -> str:
        if not ticket.human_confirmed:
            raise ExecutionBlocked(
                "refusing to submit an order that is not human_confirmed; "
                "the automated/LLM path must never place orders"
            )
        self.submitted.append(ticket)
        c = ticket.candidate
        return f"MOCK-{c.action.value}-{c.symbol}-{c.quote.strike}@{ticket.limit_price}"
