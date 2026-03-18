"""Base types for signal detection."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SignalResult:
    """Result from a single signal detector."""
    signal_name: str
    score: float              # 0.0 to 1.0
    evidence: List[str]       # Human-readable evidence snippets
    confidence: str           # "high", "medium", "low"
    sources: List[str] = field(default_factory=list)  # URLs or source descriptions
    detected_ehr: Optional[str] = None  # For ehr_confirmation signal

    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))
        if self.confidence not in ("high", "medium", "low"):
            self.confidence = "low"
