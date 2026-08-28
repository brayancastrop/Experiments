"""IV Rank / IV Percentile - the entry gate for the wheel.

This is the "star rule" of the source strategy: only sell premium when
implied volatility is *high relative to its own recent history*. Concretely:

* **IV Rank** places today's IV on a 0-100 scale between the lowest and
  highest IV seen over a lookback window (default 252 trading days ~= 1y)::

      iv_rank = (iv_now - iv_min) / (iv_max - iv_min) * 100

* **IV Percentile** is the share of days in the window whose IV was *below*
  today's IV. It is more robust to a single outlier day than IV Rank.

Off-the-shelf wheel bots filter by delta, price and open interest but happily
sell whenever there is buying power; they do not wait for volatility to be
rich. Gating on IV Rank is the value this module adds, so it must run
*before* the delta / price filters in the selector.

Everything here is pure and broker-agnostic: feed it a series of IV readings
(e.g. from IBKR historical data) and it returns numbers. A realized-volatility
helper is included as a rough *proxy* for when only prices are available -
clearly labeled, because realized vol is not implied vol.
"""

from __future__ import annotations

import math
from typing import Sequence

__all__ = [
    "InsufficientDataError",
    "iv_rank",
    "iv_percentile",
    "passes_iv_gate",
    "realized_volatility",
]

# A year of trading days. IV Rank is conventionally measured over this window.
DEFAULT_LOOKBACK = 252


class InsufficientDataError(ValueError):
    """Raised when the IV history is too short to compute a meaningful gate."""


def _window(iv_history: Sequence[float], lookback: int) -> list[float]:
    if lookback <= 0:
        raise ValueError("lookback must be positive")
    window = [float(x) for x in list(iv_history)[-lookback:]]
    if len(window) < 2:
        raise InsufficientDataError(
            f"need at least 2 IV observations, got {len(window)}"
        )
    if any(math.isnan(x) or x < 0 for x in window):
        raise ValueError("IV history must be non-negative and free of NaNs")
    return window


def iv_rank(
    current_iv: float,
    iv_history: Sequence[float],
    lookback: int = DEFAULT_LOOKBACK,
) -> float:
    """Return IV Rank in ``[0, 100]``.

    ``current_iv`` is today's implied volatility (as a fraction, e.g. ``0.35``
    for 35 %, or in vol points - only the ratio matters as long as it is
    consistent with ``iv_history``). ``iv_history`` is the recent series of the
    same measure. The value is clamped to ``[0, 100]`` so an IV that pokes
    slightly above the historical max (or below the min) does not overshoot.

    When the window is perfectly flat (``max == min``) there is no range to
    rank against, so ``0.0`` is returned - a flat, low-information regime is
    treated as "not a high-IV opportunity", which keeps the gate conservative.
    """
    window = _window(iv_history, lookback)
    lo, hi = min(window), max(window)
    if hi == lo:
        return 0.0
    rank = (float(current_iv) - lo) / (hi - lo) * 100.0
    return max(0.0, min(100.0, rank))


def iv_percentile(
    current_iv: float,
    iv_history: Sequence[float],
    lookback: int = DEFAULT_LOOKBACK,
) -> float:
    """Return IV Percentile in ``[0, 100]``.

    The fraction of observations in the window strictly below ``current_iv``,
    expressed as a percentage. Less sensitive to a lone spike than
    :func:`iv_rank`.
    """
    window = _window(iv_history, lookback)
    below = sum(1 for iv in window if iv < float(current_iv))
    return below / len(window) * 100.0


def passes_iv_gate(
    current_iv: float,
    iv_history: Sequence[float],
    threshold: float = 50.0,
    lookback: int = DEFAULT_LOOKBACK,
) -> bool:
    """True when IV Rank is at or above ``threshold`` (default 50).

    This is the boolean the selector calls before considering any contract.
    If the history is too short to judge, the gate fails closed (returns
    ``False``) rather than letting a trade through on thin evidence.
    """
    try:
        # Tolerance so an IV Rank that lands exactly on the threshold but is
        # nudged just under it by floating-point error still opens the gate.
        return iv_rank(current_iv, iv_history, lookback) >= threshold - 1e-9
    except InsufficientDataError:
        return False


def realized_volatility(
    prices: Sequence[float],
    periods_per_year: int = DEFAULT_LOOKBACK,
) -> float:
    """Annualized realized volatility from a series of closing prices.

    A *proxy* for implied volatility for when an IV feed is unavailable. It is
    the standard deviation of daily log returns scaled by
    ``sqrt(periods_per_year)``. Note this is backward-looking realized vol, not
    the forward-looking implied vol the gate really wants; use a true IV series
    when you have one.
    """
    px = [float(p) for p in prices]
    if len(px) < 2:
        raise InsufficientDataError("need at least 2 prices for realized vol")
    if any(p <= 0 for p in px):
        raise ValueError("prices must be positive")
    log_returns = [math.log(px[i] / px[i - 1]) for i in range(1, len(px))]
    n = len(log_returns)
    mean = sum(log_returns) / n
    # Sample variance (n-1) when we have more than one return.
    denom = n - 1 if n > 1 else 1
    variance = sum((r - mean) ** 2 for r in log_returns) / denom
    return math.sqrt(variance) * math.sqrt(periods_per_year)
