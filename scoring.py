"""
Score aggregation, ranking, and account model.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import SIGNAL_WEIGHTS, EHR_CONFIRMATION_BONUS, ICP_EHR_SYSTEMS
from signals.base import SignalResult


@dataclass
class AccountScore:
    """Scored account with all signal results."""
    name: str
    region: str
    raw_score: float
    final_score: float
    rank: int
    signals: Dict[str, SignalResult]
    ehr_confirmed: bool
    detected_ehr: Optional[str]
    top_signals: List[str]  # signal names sorted by weighted contribution
    notes: str = ""

    @property
    def score_pct(self) -> int:
        return int(self.final_score * 100)

    def signal_summary(self) -> List[dict]:
        """Return signals as a list of dicts for JSON serialization."""
        return [
            {
                "signal": sig_name,
                "score": round(result.score, 3),
                "weight": SIGNAL_WEIGHTS.get(sig_name, 0),
                "weighted_contribution": round(result.score * SIGNAL_WEIGHTS.get(sig_name, 0), 3),
                "confidence": result.confidence,
                "evidence": result.evidence[:2],
            }
            for sig_name, result in self.signals.items()
        ]


def compute_score(company: str, region: str, signals: Dict[str, SignalResult], notes: str = "") -> AccountScore:
    """Compute weighted score for a company given its signal results."""
    raw_score = 0.0
    ehr_confirmed = False
    detected_ehr = None

    for sig_name, result in signals.items():
        weight = SIGNAL_WEIGHTS.get(sig_name, 0.0)
        raw_score += result.score * weight

        if sig_name == "ehr_confirmation" and result.score > 0.5:
            ehr_confirmed = True
            detected_ehr = result.detected_ehr

    # Apply EHR confirmation bonus
    final_score = raw_score * EHR_CONFIRMATION_BONUS if ehr_confirmed else raw_score
    final_score = min(final_score, 1.0)

    # Sort signals by weighted contribution (descending)
    top_signals = sorted(
        SIGNAL_WEIGHTS.keys(),
        key=lambda s: signals[s].score * SIGNAL_WEIGHTS[s] if s in signals else 0,
        reverse=True,
    )

    return AccountScore(
        name=company,
        region=region,
        raw_score=raw_score,
        final_score=final_score,
        rank=0,  # assigned after sorting
        signals=signals,
        ehr_confirmed=ehr_confirmed,
        detected_ehr=detected_ehr,
        top_signals=top_signals,
        notes=notes,
    )


def rank_accounts(accounts: List[AccountScore]) -> List[AccountScore]:
    """Sort accounts by final score and assign ranks."""
    sorted_accounts = sorted(accounts, key=lambda a: a.final_score, reverse=True)
    for i, account in enumerate(sorted_accounts, 1):
        account.rank = i
    return sorted_accounts
