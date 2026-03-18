# Solv Health Account Intelligence System — Architecture & Conventions

## System Overview

This system accepts a list of urgent care company names and a region, detects 7 buying signals from public data for each account, scores and ranks them by likelihood to buy Solv's AI front desk automation, and generates sales-ready account briefs for the top accounts.

**Primary use case:** Replace manual account research for the sales team. Run on a weekly schedule, output prioritized accounts with evidence.

---

## Architecture

```
main.py                     CLI entry point, orchestrates the pipeline
config.py                   Signal weights and system settings (adjust here)
signals/
  base.py                   SignalResult dataclass
  detector.py               SerpAPI-based signal detection (one method per signal)
scoring.py                  Weighted score computation and ranking
briefs.py                   Claude API brief generation + Google Docs prompt fetch
demo_data.py                Pre-computed demo dataset (3 real accounts)
output/
  accounts_ranked.json      Machine-readable ranked output
  accounts_ranked.md        Human-readable ranked output
  briefs/                   One Markdown file per generated account brief
```

**Data flow:**
1. Input: company names + region
2. `SignalDetector.detect_all()` → 7 `SignalResult` objects per company (via SerpAPI)
3. `compute_score()` → `AccountScore` with weighted final score
4. `rank_accounts()` → sorted list
5. `generate_brief()` → Claude API brief (optional, for top N accounts)

---

## Signal Weights & Rationale

Weights live in `config.py` → `SIGNAL_WEIGHTS`. They should be updated as the sales team learns which signals actually correlate with closed deals.

| Signal | Weight | Rationale |
|--------|--------|-----------|
| `ehr_migration` | 0.25 | Strongest buying signal — EHR go-live or migration creates a 12-24 month window where front desk friction peaks. Switching costs are high but vendor consolidation is actively on the table. |
| `leadership_hire` | 0.20 | New VP Ops / COO / Director of Operations in the past 90 days. New leaders audit existing tools, have mandate to improve, and don't have switching cost baggage. |
| `job_postings` | 0.18 | High volume of front-desk/receptionist postings, especially "urgently hiring." Turnover at the front desk is a direct consequence of system-driven workflow friction — the exact problem Solv solves. |
| `ma_activity` | 0.15 | PE acquisition, M&A, or roll-up. Post-acquisition integration creates EHR fragmentation, new operational mandates, and budget for tech that standardizes workflows across locations. |
| `patient_reviews` | 0.12 | Reviews citing hold times, no answer, check-in delays, system issues. Quantifies the patient-facing impact of front desk overload — useful to reference in outreach. |
| `expansion_news` | 0.05 | New location openings. Growing operators are adding complexity faster than their current intake process can scale — creates urgency. Lower weight because growth alone doesn't indicate pain. |
| `ehr_confirmation` | 0.05 | Confirms athenahealth, Experity, or eClinicalWorks. These are Solv's supported EHRs. Presence triggers a 15% score bonus. Absence doesn't disqualify but should be noted. |

**EHR Confirmation Bonus:** If `ehr_confirmation` fires, the total score is multiplied by 1.15. This reflects the reality that integration feasibility is a hard prerequisite — a high-signal account on an unsupported EHR cannot close.

---

## Adding a New Signal

1. Add a `detect_<signal_name>` method to `signals/detector.py` following the same pattern:
   - Input: `company: str`, `region: str`
   - Returns: `SignalResult` with `score` (0-1), `evidence` list, `confidence`
   - Use `self._search(query)` for SerpAPI queries
   - Score heuristic: 0.0 = no signal, 1.0 = strong confirmed signal

2. Add the signal to `detect_all()` in `detector.py`

3. Add a weight in `config.py → SIGNAL_WEIGHTS` (adjust other weights proportionally so they still sum to 1.0)

4. Add realistic demo data to `demo_data.py` for all 3 demo accounts

5. Update this CLAUDE.md with the new signal's rationale

**Example signals to consider adding:**
- `negative_glassdoor`: High Glassdoor complaints about "systems" or "technology"
- `conference_sponsorship`: Company speaking at MGMA, UCAOA — ops leaders who are already thinking about solutions
- `webinar_registration`: Registration for operational efficiency or front desk automation webinars

---

## Updating Signal Weights

**The weights in `config.py` should be treated as hypotheses until validated by closed deal data.**

Process for updating weights:
1. After each closed deal, the sales team records which signals were present and their scores
2. After ~20 closed deals, compare signal presence rates to win rates
3. Increase weights for signals with high correlation, decrease for low-correlation signals
4. Re-normalize so weights sum to 1.0

Current weights reflect pre-launch priors based on ICP analysis. The `ehr_migration` and `leadership_hire` weights are likely to remain high — these are structural buying moments. `patient_reviews` may need to be increased if it proves more predictive than expected.

---

## Google Docs System Prompt

The Claude brief generation system prompt is fetched at runtime from Google Doc ID `1xyq-5l397SaX3cyhaOjekxGlFOFUo9X8HpgwUeXBe8g`. This allows the sales team to update:
- ICP definition
- Value propositions and messaging
- Objection handling guidance
- Outreach tone and format

To update: edit the Google Doc directly. No code changes needed.
Requires `GOOGLE_API_KEY` and `GOOGLE_DOCS_ID` in `.env`. Falls back to the hardcoded prompt in `briefs.py` if unavailable.

---

## Running on a Schedule

The system is designed to run weekly. Recommended setup with cron:

```bash
# Run every Monday at 7 AM
0 7 * * 1 cd /path/to/repo && python main.py --companies-file accounts.txt --region "Southeast" --briefs >> logs/weekly_run.log 2>&1
```

Or use a workflow scheduler (GitHub Actions, Airflow, etc.) with the same command.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | For briefs | Claude API key |
| `SERPAPI_KEY` | For live mode | SerpAPI key for Google searches |
| `GOOGLE_DOCS_ID` | Optional | Google Doc ID for system prompt |
| `GOOGLE_API_KEY` | Optional | Google API key for Docs access |

Copy `.env.example` to `.env` and fill in keys. Never commit `.env`.

---

## Demo Mode

`python main.py --demo` runs without any API keys using pre-computed signal data for 3 real accounts. Use `--demo --briefs` to also generate Claude briefs (requires `ANTHROPIC_API_KEY`).

Demo accounts:
- **MedRite Urgent Care** (eCW, NYC) — Zocdoc/eCW sync failures, 134 negative reviews, RCM analyst hiring
- **Xpress Wellness / Integrity Urgent Care** (Experity + eCW, OK/TX) — dual-EHR environment, heavy front-desk posting volume
- **MainStreet Family Care** (athenahealth, Southeast) — high-friction portal intake, COO with Lean focus
