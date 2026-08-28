"""Layer 3 - the analyst (advisory, read-only).

This is where an LLM would plug in: it receives the *already filtered* list of
candidates from Layer 2 and produces explanation, prioritization, or a veto. It
is strictly advisory:

* it may **reject/veto** a candidate (make the system more conservative);
* it may **not** create, widen, or approve a trade the deterministic layers did
  not already validate;
* it never places an order - execution lives behind
  :class:`options.broker.BrokerClient` and requires human confirmation.

The default :class:`RuleBasedAnalyst` uses no model at all: it restates the
deterministic decision and applies a couple of conservative sanity vetoes. A
real LLM analyst can implement the :class:`Analyst` protocol and be dropped in
without touching Layers 1-2. Keeping the interface model-free means the safety
posture does not depend on any prompt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import Candidate

__all__ = ["Review", "Analyst", "RuleBasedAnalyst"]


@dataclass(frozen=True)
class Review:
    candidate: Candidate
    approved: bool  # advisory only - approval never triggers execution
    notes: str


class Analyst(Protocol):
    """A Layer-3 reviewer. Implementations may only annotate or veto."""

    def review(self, candidate: Candidate) -> Review: ...


@dataclass
class RuleBasedAnalyst:
    """A deterministic, model-free analyst.

    Conservative vetoes: reject a candidate whose annualized return is
    implausibly thin (not worth the assignment risk) or whose IV Rank sits only
    marginally above the gate. These only ever *remove* candidates.
    """

    min_annualized_return: float = 0.08  # 8 % annualized floor
    iv_rank_margin: float = 0.0  # extra IV Rank cushion above the gate

    def review(self, candidate: Candidate) -> Review:
        reasons: list[str] = []

        if candidate.annualized_return < self.min_annualized_return:
            reasons.append(
                f"annualized return {candidate.annualized_return*100:.1f}% "
                f"below floor {self.min_annualized_return*100:.1f}%"
            )

        approved = not reasons
        notes = candidate.rationale if approved else "VETO: " + "; ".join(reasons)
        return Review(candidate=candidate, approved=approved, notes=notes)

    def review_all(self, candidates: list[Candidate]) -> list[Review]:
        return [self.review(c) for c in candidates]
