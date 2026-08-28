"""Position sizing and the hard risk limits of Layer 1.

These functions encode the limits the source strategy insists on and that the
advisory LLM layer must never be able to loosen:

* **Cash-secured only.** A short put ties up ``strike * 100`` in cash. Unless
  ``allow_margin`` is explicitly set, a put that cannot be fully cash-secured
  is rejected.
* **Tiered concentration.** No single position may exceed the max-position
  percentage for the account's size band (e.g. 20 % small, 5 % above $25k).
* **Contract caps.** At most ``max_contracts_per_symbol`` per symbol.
"""

from __future__ import annotations

from .config import SizingTier, WheelConfig
from .models import AccountState, OptionQuote

__all__ = [
    "csp_collateral",
    "max_position_pct",
    "max_position_value",
    "can_afford_csp",
    "contracts_for_csp",
    "shares_backing_calls",
    "contracts_for_covered_call",
]

# Standard US equity option multiplier.
CONTRACT_MULTIPLIER = 100


def csp_collateral(strike: float, contracts: int = 1) -> float:
    """Cash required to secure ``contracts`` short puts at ``strike``."""
    return float(strike) * CONTRACT_MULTIPLIER * contracts


def max_position_pct(net_liquidation: float, tiers: tuple[SizingTier, ...]) -> float:
    """Max fraction of net liquidation for one position at this account size.

    Picks the highest tier whose ``min_net_liquidation`` the account meets.
    """
    applicable = [t for t in tiers if net_liquidation >= t.min_net_liquidation]
    if not applicable:
        # Below the smallest tier's floor: fall back to the most conservative.
        return min(t.max_position_pct for t in tiers)
    # The tier with the highest floor we still clear governs.
    return max(applicable, key=lambda t: t.min_net_liquidation).max_position_pct


def max_position_value(
    account: AccountState,
    config: WheelConfig,
    symbol: str | None = None,
) -> float:
    """Dollar cap for a single position, honoring any per-symbol override."""
    pct = max_position_pct(account.net_liquidation, config.sizing_tiers)
    if symbol is not None:
        override = config.for_symbol(symbol).max_position_pct
        if override is not None:
            pct = override
    return account.net_liquidation * pct


def can_afford_csp(
    account: AccountState,
    quote: OptionQuote,
    config: WheelConfig,
    contracts: int = 1,
) -> bool:
    """Whether the account may sell ``contracts`` cash-secured puts on ``quote``.

    Enforces, in order: the no-margin rule (collateral <= cash buying power),
    and the per-position concentration cap.
    """
    collateral = csp_collateral(quote.strike, contracts)

    if not config.allow_margin and collateral > account.buying_power:
        return False

    if collateral > max_position_value(account, config, quote.symbol):
        return False

    return True


def contracts_for_csp(
    account: AccountState,
    quote: OptionQuote,
    config: WheelConfig,
) -> int:
    """Largest affordable CSP size, capped by config and risk limits.

    Bounded by cash buying power, the per-position dollar cap, and
    ``max_contracts_per_symbol``. Returns ``0`` when even one contract fails
    the affordability check.
    """
    if not can_afford_csp(account, quote, config, contracts=1):
        return 0

    per_contract = csp_collateral(quote.strike, 1)
    if per_contract <= 0:
        return 0

    by_cash = (
        int(account.buying_power // per_contract)
        if not config.allow_margin
        else config.max_contracts_per_symbol
    )
    by_position_cap = int(
        max_position_value(account, config, quote.symbol) // per_contract
    )
    hard_cap = config.max_contracts_per_symbol

    return max(0, min(by_cash, by_position_cap, hard_cap))


def shares_backing_calls(account: AccountState, symbol: str) -> int:
    """How many covered calls the current share holding backs (100 shares each)."""
    return account.shares_owned.get(symbol, 0) // CONTRACT_MULTIPLIER


def contracts_for_covered_call(
    account: AccountState,
    quote: OptionQuote,
    config: WheelConfig,
) -> int:
    """Covered-call size: backed by owned shares, capped per symbol."""
    backed = shares_backing_calls(account, quote.symbol)
    return max(0, min(backed, config.max_contracts_per_symbol))
