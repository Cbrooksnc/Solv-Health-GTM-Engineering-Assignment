# Solv Health Account Intelligence System

Detects buying signals for urgent care operators and generates sales-ready account briefs. Replaces manual account research for the sales team.

## Quick Start (No API Keys)

```bash
git clone https://github.com/Cbrooksnc/Solv-Health-GTM-Engineering-Assignment
cd Solv-Health-GTM-Engineering-Assignment
pip install -r requirements.txt
python main.py --demo
```

Add `--briefs` to also generate Claude-written account briefs (requires `ANTHROPIC_API_KEY`).

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment

> Skip this step if you only want to run `--demo` (no briefs). API keys are only needed for brief generation and live signal detection.

Create a `.env` file in the project root:

**Mac/Linux:**
```bash
cp .env.example .env
```

**Windows:**
```powershell
copy .env.example .env
```

Then open `.env` in any text editor and fill in the keys you need:

```
ANTHROPIC_API_KEY=sk-ant-...   # required for --briefs
SERPAPI_KEY=...                 # required for live mode
```

Get keys here:
- `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com) (requires credits)
- `SERPAPI_KEY` — [serpapi.com](https://serpapi.com) (free tier available)

### 3. Run

First, make sure you're in the project directory:

**Mac/Linux:**
```bash
cd Solv-Health-GTM-Engineering-Assignment
```

**Windows:**
```powershell
cd C:\Users\<your-username>\Solv-Health-GTM-Engineering-Assignment
```

**Demo mode** (no API keys required):
```bash
python main.py --demo
python main.py --demo --briefs   # with AI-written briefs (requires ANTHROPIC_API_KEY)
```

**Live mode** (requires `SERPAPI_KEY`):
```bash
python main.py --companies "MedRite Urgent Care, CityMD" --region "New York" --briefs
python main.py --companies-file accounts.txt --region "Southeast" --top 5 --briefs
```

---

## CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--demo` | Run with cached demo data, no API keys needed | — |
| `--companies` | Comma-separated company names | — |
| `--companies-file` | Path to file with one company per line | — |
| `--region` | Geographic focus for searches | — |
| `--briefs` | Generate AI account briefs for top accounts | off |
| `--top N` | Number of accounts to generate briefs for | 3 |

---

## What It Detects

7 buying signals, each weighted by predictive value:

| Signal | Weight | What It Indicates |
|--------|--------|-------------------|
| EHR Migration | 0.25 | Go-live or migration in progress — 12-24 month buying window |
| Leadership Hire | 0.20 | New VP Ops / COO / Director in past 90 days |
| Job Postings | 0.18 | High front-desk/receptionist posting volume |
| M&A Activity | 0.15 | PE acquisition, roll-up, post-merger integration |
| Patient Reviews | 0.12 | Reviews citing hold times, check-in delays, system issues |
| Expansion News | 0.05 | New location openings |
| EHR Confirmation | 0.05 | Confirms athena/Experity/eCW (triggers 15% score bonus) |

---

## Output

All output is written to the `output/` directory:

- `output/accounts_ranked.json` — Machine-readable ranked accounts with all signal data
- `output/accounts_ranked.md` — Human-readable ranked summary
- `output/briefs/<account_name>_brief.md` — One brief per top account

---

## Architecture

```
main.py              CLI entry point + rich terminal output
config.py            Signal weights (adjust as you learn which signals predict closes)
signals/
  base.py            SignalResult dataclass
  detector.py        SerpAPI-based detection (one method per signal)
scoring.py           Weighted scoring and ranking
briefs.py            Claude API brief generation + Google Docs system prompt
demo_data.py         Pre-computed data for 3 real accounts
```

See `CLAUDE.md` for full architecture docs, how to add signals, and weight update process.

---

## Extending the System

### Add a new signal
1. Add a `detect_<name>` method to `signals/detector.py`
2. Register it in `detect_all()`
3. Add weight to `config.py`
4. Add demo data to `demo_data.py`

### Update signal weights
Edit `SIGNAL_WEIGHTS` in `config.py`. Weights should be updated after ~20 closed deals to reflect which signals actually correlated with wins. See `CLAUDE.md` for the full process.

### Update the brief system prompt
Edit the Google Doc linked in your `.env` (`GOOGLE_DOCS_ID`). The sales team can update ICP, messaging, and value props without touching code. Falls back to the hardcoded prompt in `briefs.py` if unavailable.

---

## API Keys

| Key | Source | Required For |
|-----|--------|-------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Brief generation |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) | Live signal detection |
| `GOOGLE_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) | Dynamic system prompt |
