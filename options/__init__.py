"""Options "Wheel" strategy engine (experiment).

A small, deterministic engine for the wheel strategy: selling cash-secured
puts (CSPs) and covered calls only, cash-secured, **zero margin**.

Design (three layers), mirroring the architecture worked out in the source
conversation:

* **Layer 1 - deterministic execution** (no LLM): :mod:`options.iv_rank`,
  :mod:`options.sizing`, :mod:`options.selector`. Hard limits live here.
* **Layer 2 - scanner + rules**: :mod:`options.scanner` turns market data
  into a ranked list of candidates.
* **Layer 3 - analyst** (advisory, read-only, optional):
  :mod:`options.analyst`. It may explain, rank or *veto* candidates but can
  never place an order.

The IV-Rank gate (:mod:`options.iv_rank`) is the piece that off-the-shelf
wheel bots (thetagang, alpaca options-wheel, ...) do not provide out of the
box; it is the centerpiece of this experiment.

Nothing here connects to a live broker. Order *proposals* are produced; a
real IBKR/ib_async execution path is intentionally left as an interface
(:class:`options.broker.BrokerClient`) so a human stays on the trigger.
"""

from .iv_rank import iv_rank, iv_percentile, passes_iv_gate, realized_volatility
from .models import (
    Action,
    AccountState,
    Candidate,
    OptionQuote,
    OptionRight,
    SymbolMarketData,
)
from .config import WheelConfig, SymbolConfig, SizingTier
from .sizing import (
    csp_collateral,
    max_position_pct,
    max_position_value,
    can_afford_csp,
    contracts_for_csp,
)
from .selector import select_put, select_call
from .scanner import scan

__all__ = [
    "iv_rank",
    "iv_percentile",
    "passes_iv_gate",
    "realized_volatility",
    "Action",
    "AccountState",
    "Candidate",
    "OptionQuote",
    "OptionRight",
    "SymbolMarketData",
    "WheelConfig",
    "SymbolConfig",
    "SizingTier",
    "csp_collateral",
    "max_position_pct",
    "max_position_value",
    "can_afford_csp",
    "contracts_for_csp",
    "select_put",
    "select_call",
    "scan",
]
