"""
Signal weights and system configuration.
Weights should be tuned based on sales team feedback on closed deals.
See CLAUDE.md for rationale on each weight.
"""

# Signal weights — must sum to 1.0
# Adjust these based on which signals correlate most with closed deals
SIGNAL_WEIGHTS = {
    "ehr_migration": 0.25,      # Strongest signal — 12-24 month buying window
    "job_postings": 0.18,       # High volume front-desk/receptionist hiring
    "leadership_hire": 0.20,    # New VP Ops, COO, Director of Operations (90-day window)
    "ma_activity": 0.15,        # PE acquisition, M&A, roll-up
    "patient_reviews": 0.12,    # Reviews citing hold times, check-in delays, system issues
    "expansion_news": 0.05,     # New location openings, franchise expansion
    "ehr_confirmation": 0.05,   # Confirms athena/Experity/eCW (ICP gate)
}

# EHR confirmation bonus — multiplier applied to total score if target EHR confirmed
EHR_CONFIRMATION_BONUS = 1.15  # 15% score boost for confirmed ICP EHR

# ICP EHR systems — presence of these triggers the bonus
ICP_EHR_SYSTEMS = ["athenahealth", "athena", "experity", "eclinicalworks", "ecw"]

# Minimum score threshold to include account in ranked output
MIN_SCORE_THRESHOLD = 0.0

# Default number of accounts to generate briefs for
DEFAULT_TOP_N = 3

# SerpAPI search settings
SERPAPI_NUM_RESULTS = 10
SERPAPI_MAX_SEARCHES_PER_SIGNAL = 2

# Google Docs ID for system prompt (sales team can update without touching code)
GOOGLE_DOCS_ID = "1xyq-5l397SaX3cyhaOjekxGlFOFUo9X8HpgwUeXBe8g"

# Claude model for brief generation
CLAUDE_MODEL = "claude-sonnet-4-6"

# Brief generation settings
BRIEF_MAX_TOKENS = 2000

# Output directories
OUTPUT_DIR = "output"
BRIEFS_DIR = "output/briefs"
