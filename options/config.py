"""Declarative configuration for the wheel engine.

Everything the source strategy calls a "rule" is a parameter here: the IV-Rank
threshold, target delta / DTE, open-interest and premium floors, strike buffer,
per-tier position sizing, per-symbol overrides, and the hard caps (no margin,
max new contracts per run).

Config loads from TOML via the standard-library ``tomllib`` (Python >= 3.11),
so there is no third-party dependency just to read settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

__all__ = ["SizingTier", "SymbolConfig", "WheelConfig", "ResolvedSymbolConfig"]


@dataclass(frozen=True)
class SizingTier:
    """Max fraction of net liquidation allowed in a single position.

    ``min_net_liquidation`` is the lower bound (inclusive) of the account-size
    band this tier applies to. Small accounts concentrate (e.g. 20 %); larger
    accounts diversify (e.g. 5 % above $25k), matching the source strategy.
    """

    min_net_liquidation: float
    max_position_pct: float


# Default sizing ladder from the source strategy: concentrated while small,
# diversified once the account clears $25k.
DEFAULT_SIZING_TIERS: tuple[SizingTier, ...] = (
    SizingTier(min_net_liquidation=0.0, max_position_pct=0.20),
    SizingTier(min_net_liquidation=25_000.0, max_position_pct=0.05),
)


@dataclass(frozen=True)
class SymbolConfig:
    """Per-symbol overrides. Any ``None`` field falls back to the global value."""

    target_delta: float | None = None
    target_dte: int | None = None
    min_dte: int | None = None
    max_dte: int | None = None
    min_open_interest: int | None = None
    min_premium: float | None = None
    max_position_pct: float | None = None


@dataclass(frozen=True)
class ResolvedSymbolConfig:
    """A fully resolved parameter set for one symbol (no ``None`` values)."""

    target_delta: float
    target_dte: int
    min_dte: int
    max_dte: int
    min_open_interest: int
    min_premium: float
    strike_buffer_pct: float
    iv_rank_threshold: float
    iv_lookback_days: int
    max_position_pct: float | None  # None -> use sizing tiers


@dataclass(frozen=True)
class WheelConfig:
    # --- entry gate (the star rule) ---
    iv_rank_threshold: float = 50.0
    iv_lookback_days: int = 252

    # --- contract selection ---
    target_delta: float = 0.30  # sell puts/calls near |delta| ~ 0.20-0.30
    target_dte: int = 30
    min_dte: int = 25
    max_dte: int = 45
    min_open_interest: int = 100
    min_premium: float = 0.10  # per share; * 100 for per-contract dollars
    strike_buffer_pct: float = 0.05  # puts: strike <= price * (1 + buffer)

    # --- hard limits (never relaxed by the LLM layer) ---
    allow_margin: bool = False  # cash-secured only
    max_new_contracts_per_run: int = 3
    max_contracts_per_symbol: int = 1  # one contract/symbol keeps risk legible

    sizing_tiers: tuple[SizingTier, ...] = DEFAULT_SIZING_TIERS
    symbols: dict[str, SymbolConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sizing_tiers:
            raise ValueError("at least one sizing tier is required")
        if not (0 <= self.iv_rank_threshold <= 100):
            raise ValueError("iv_rank_threshold must be within [0, 100]")
        if self.min_dte > self.max_dte:
            raise ValueError("min_dte must be <= max_dte")

    # -- resolution -----------------------------------------------------
    def for_symbol(self, symbol: str) -> ResolvedSymbolConfig:
        """Merge global defaults with any per-symbol override."""
        override = self.symbols.get(symbol, SymbolConfig())
        pick = lambda o, g: g if o is None else o  # noqa: E731
        return ResolvedSymbolConfig(
            target_delta=pick(override.target_delta, self.target_delta),
            target_dte=pick(override.target_dte, self.target_dte),
            min_dte=pick(override.min_dte, self.min_dte),
            max_dte=pick(override.max_dte, self.max_dte),
            min_open_interest=pick(override.min_open_interest, self.min_open_interest),
            min_premium=pick(override.min_premium, self.min_premium),
            strike_buffer_pct=self.strike_buffer_pct,
            iv_rank_threshold=self.iv_rank_threshold,
            iv_lookback_days=self.iv_lookback_days,
            max_position_pct=override.max_position_pct,
        )

    # -- loading --------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WheelConfig":
        data = dict(data)
        tiers = data.pop("sizing_tiers", None)
        symbols_raw = data.pop("symbols", None)

        cfg = cls(**data)

        if tiers is not None:
            parsed = tuple(
                SizingTier(
                    min_net_liquidation=float(t["min_net_liquidation"]),
                    max_position_pct=float(t["max_position_pct"]),
                )
                for t in tiers
            )
            cfg = replace(cfg, sizing_tiers=parsed)

        if symbols_raw is not None:
            symbols = {
                sym: SymbolConfig(**overrides) for sym, overrides in symbols_raw.items()
            }
            cfg = replace(cfg, symbols=symbols)

        return cfg

    @classmethod
    def from_toml(cls, path: str) -> "WheelConfig":
        import tomllib  # stdlib in Python 3.11+

        with open(path, "rb") as fh:
            data = tomllib.load(fh)
        return cls.from_dict(data)
