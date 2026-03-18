"""
Account brief generation using the Anthropic API.
System prompt is fetched from a Google Doc at runtime so the sales team
can update ICP, messaging, and value props without touching code.
Falls back to hardcoded defaults if the doc is unavailable.
"""
import os
import json
from typing import Optional

import anthropic

from config import CLAUDE_MODEL, BRIEF_MAX_TOKENS, GOOGLE_DOCS_ID

# Hardcoded fallback system prompt
FALLBACK_SYSTEM_PROMPT = """You are a senior sales intelligence analyst for Solv Health, a company that sells AI-powered front desk automation to multi-site urgent care operators.

Solv's ICP: Urgent care groups with 5+ locations running athenahealth, Experity, or eClinicalWorks (eCW) as their EHR. Solv is most successful when operations leaders are struggling with:
- High inbound call volumes and front desk overload
- Patient check-in friction and long wait times
- Front desk staff turnover driven by system frustration
- Visit volume growth that outpaces manual intake capacity

Solv's core value props:
1. AI-powered phone intake: Answers 100% of inbound calls, books appointments, handles FAQs
2. Digital check-in: Eliminates paper and reduces front desk workload by 60%
3. EHR-native integration: Direct integration with athena, Experity, and eCW — no double-entry
4. ROI: Reduces front desk FTE need, cuts call abandonment, improves patient satisfaction scores

When writing account briefs:
- Lead with THEIR world, not ours — what is the prospect experiencing right now?
- Be specific — use the evidence from our signal detection, not generic pain points
- The outreach message should feel like it came from someone who did their homework, not a template
- Tone: Direct, peer-to-peer, no buzzwords. These are operations leaders who are skeptical of vendor pitches.
- Format in clean Markdown with clear sections"""


def fetch_google_doc_prompt(doc_id: str, api_key: str) -> Optional[str]:
    """Fetch system prompt from Google Doc. Returns None if unavailable."""
    try:
        import urllib.request
        url = f"https://docs.googleapis.com/v1/documents/{doc_id}?key={api_key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            # Extract plain text from Google Docs API response
            content = data.get("body", {}).get("content", [])
            text_parts = []
            for element in content:
                paragraph = element.get("paragraph", {})
                for pe in paragraph.get("elements", []):
                    text_run = pe.get("textRun", {})
                    text_parts.append(text_run.get("content", ""))
            return "".join(text_parts).strip() or None
    except Exception:
        return None


def get_system_prompt() -> str:
    """Get system prompt from Google Doc, with fallback to hardcoded default."""
    doc_id = os.environ.get("GOOGLE_DOCS_ID", GOOGLE_DOCS_ID)
    api_key = os.environ.get("GOOGLE_API_KEY", "")

    if doc_id and api_key:
        prompt = fetch_google_doc_prompt(doc_id, api_key)
        if prompt and len(prompt) > 100:
            return prompt

    return FALLBACK_SYSTEM_PROMPT


def generate_brief(account, system_prompt: Optional[str] = None) -> str:
    """
    Generate a sales-ready account brief using Claude.

    Args:
        account: AccountScore object with signals and scores
        system_prompt: Override system prompt (uses get_system_prompt() if None)

    Returns:
        Markdown-formatted brief as a string
    """
    if system_prompt is None:
        system_prompt = get_system_prompt()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build signal evidence summary for the prompt
    signal_evidence = []
    for sig_name, result in account.signals.items():
        if result.score > 0.2 and result.evidence:
            weight = account.signals[sig_name].score
            signal_evidence.append(
                f"**{sig_name.replace('_', ' ').title()}** (score: {result.score:.2f}):\n"
                + "\n".join(f"  - {e}" for e in result.evidence[:2])
            )

    evidence_block = "\n\n".join(signal_evidence) if signal_evidence else "Limited signal data available."

    user_prompt = f"""Generate a sales-ready account brief for the following urgent care company. Use the signal evidence provided — be specific, not generic.

## Account: {account.name}
**Region:** {account.region}
**Overall Buying Signal Score:** {account.score_pct}/100
**EHR Confirmed:** {account.detected_ehr if account.detected_ehr else 'Unknown'}
{f'**Notes:** {account.notes}' if account.notes else ''}

## Signal Evidence Detected:
{evidence_block}

## Top Signals by Weighted Impact:
{', '.join(account.top_signals[:4])}

---

Please generate a structured account brief with these sections:

1. **Company Snapshot** — Size, locations, EHR system, market position
2. **Why They're Likely to Buy Right Now** — Specific to their current signals
3. **Pain Points Your Signals Suggest** — Concrete, evidence-based framing
4. **Recommended Outreach Angle** — How to frame the conversation
5. **Personalized Outreach Message** — A ready-to-send email or LinkedIn message (150-200 words) that leads with their world

Make the outreach message feel earned — reference specific things you found. Do not use generic opener lines."""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=BRIEF_MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return next(
        (block.text for block in response.content if block.type == "text"),
        "Brief generation failed."
    )
