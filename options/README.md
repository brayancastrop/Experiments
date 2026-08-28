# Options Wheel Engine (experiment)

A small, deterministic engine for the **wheel** options strategy: sell
cash-secured puts (CSPs) and covered calls only, cash-secured, **zero margin**,
and only when implied volatility is rich (IV Rank gate). It turns market data
into ranked trade *proposals* — it does **not** place orders.

This is the code sketch of the architecture worked out in the source
conversation that inspired it. It deliberately keeps the machine that could
touch real money (broker execution) behind an interface, with a human on the
trigger.

## Why this exists / DRY note

Mature open-source wheel bots already exist — `thetagang` (IBKR, AGPL),
`alpacahq/options-wheel`, `AllYouNeedIsWheel`. They solve broker connection,
market data, and order plumbing. The one thing none of them ships as a
first-class feature is the strategy's **star rule**: *only sell when IV Rank is
high*. So this repo:

- **reuses** the idea of `ib_async` for the eventual IBKR adapter (that library
  is the DRY win — don't re-write IBKR connectivity), and treats `thetagang`'s
  `find_eligible_contracts` as a **reference spec**, not a dependency (its AGPL
  license is viral);
- **adds** the missing piece — a clean, tested `iv_rank` module — plus tiered
  sizing by account size and an explicit no-margin limit.

## Three-layer architecture

| Layer | Module(s) | Role | LLM? |
|-------|-----------|------|------|
| **1 — Execution rules** | `iv_rank.py`, `sizing.py`, `selector.py` | IV-Rank gate, contract filters, hard cash/size limits | No — deterministic |
| **2 — Scanner** | `scanner.py` | Rank surviving candidates, apply per-run budget | No — deterministic |
| **3 — Analyst** | `analyst.py` | Explain / prioritize / **veto** candidates | Optional, advisory only |

The **broker boundary** (`broker.py`) sits under Layer 1: a `BrokerClient`
protocol plus an in-memory `MockBroker`. Execution is fenced off — `place_order`
refuses any ticket that is not `human_confirmed`, so "the LLM never pulls the
trigger" is structural, not just a comment.

```
market data ──▶ [L1] IV-Rank gate ─▶ strike/DTE/delta/OI filters ─▶ sizing & hard limits
                                                                          │
                                                          proposals ◀─────┘
                                                                          │
                          [L2] rank by annualized return, cap per run ────┤
                                                                          │
                          [L3] analyst annotates / vetoes (never approves into an order)
                                                                          │
                          human confirms ──▶ broker.place_order(...)  (out of scope here)
```

## The IV-Rank gate (the centerpiece)

```
iv_rank = (iv_now - iv_min) / (iv_max - iv_min) * 100      # over ~252 days
```

Sell only when `iv_rank >= threshold` (default 50). `iv_percentile` (share of
days below today's IV) is also provided as a more outlier-robust alternative,
and `realized_volatility` as a rough proxy when no IV feed is available. The
gate runs **before** the delta/price filters — that ordering is the whole point.

## Layout

```
options/
├── iv_rank.py           # IV Rank / IV Percentile / gate  (the star rule)
├── models.py            # OptionQuote, AccountState, Candidate, ...
├── config.py            # WheelConfig + TOML loader + per-symbol overrides
├── sizing.py            # tiered position caps, CSP collateral, no-margin limit
├── selector.py          # find_eligible_contracts + IV-Rank gate
├── scanner.py           # Layer 2: ranked candidate list
├── broker.py            # BrokerClient protocol + MockBroker (no real orders)
├── analyst.py           # Layer 3: advisory, read-only reviewer
├── config.example.toml  # every rule as a parameter
├── requirements.txt     # stdlib-only core; ib_async only for a real adapter
├── examples/run_scan.py # end-to-end demo against the mock broker
└── tests/               # unittest suite (stdlib only)
```

## Run it

Everything runs on the Python 3.11+ standard library — nothing to install.

```bash
# from the repository root
python -m unittest discover -s options/tests -t .   # tests
python -m options.examples.run_scan                 # end-to-end demo
```

## Scope & safety

- **No live trading.** There is no real broker connection and no automated
  order path. The engine outputs proposals; a real IBKR adapter (via
  `ib_async`) behind `BrokerClient` is left as an exercise, gated by human
  confirmation and the hard limits in `sizing.py`.
- **Not financial advice.** This is an experiment in encoding a rule set, not a
  recommendation to trade it. The historical "returns" that motivated the
  strategy were heavily inflated by outside capital contributions, not the
  method itself — the value here is the disciplined, testable rule set, not any
  promised performance.
