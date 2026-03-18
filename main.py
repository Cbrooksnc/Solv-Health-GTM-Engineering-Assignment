"""
Solv Health Account Intelligence System
Run `python main.py --help` for usage.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.markdown import Markdown
from rich import box

load_dotenv()

from config import (
    SIGNAL_WEIGHTS, DEFAULT_TOP_N, MIN_SCORE_THRESHOLD,
    OUTPUT_DIR, BRIEFS_DIR
)
from signals.base import SignalResult
from signals.detector import SignalDetector
from scoring import AccountScore, compute_score, rank_accounts

console = Console()

# ─────────────────────────────────────────────
# Output helpers
# ─────────────────────────────────────────────

SCORE_COLOR = {
    (80, 101): "bold green",
    (60, 80): "green",
    (40, 60): "yellow",
    (0, 40): "red",
}

def score_color(pct: int) -> str:
    for (lo, hi), color in SCORE_COLOR.items():
        if lo <= pct < hi:
            return color
    return "white"


def signal_bar(score: float, width: int = 20) -> str:
    filled = int(score * width)
    return "█" * filled + "░" * (width - filled)


def print_header():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Solv Health Account Intelligence System[/bold cyan]\n"
        "[dim]Buying signal detection for urgent care operators[/dim]",
        border_style="cyan",
    ))
    console.print()


def print_ranked_table(accounts: List[AccountScore]):
    table = Table(
        title="[bold]Ranked Accounts by Buying Signal Score[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    table.add_column("Rank", justify="center", width=6)
    table.add_column("Account", min_width=28)
    table.add_column("Region", min_width=18)
    table.add_column("EHR", min_width=16)
    table.add_column("Score", justify="center", width=8)
    table.add_column("Signal Strength", min_width=22)
    table.add_column("Top Signal", min_width=18)

    for acct in accounts:
        color = score_color(acct.score_pct)
        ehr_display = acct.detected_ehr or "[dim]Unknown[/dim]"
        top_signal = acct.top_signals[0].replace("_", " ").title() if acct.top_signals else "-"
        bar = signal_bar(acct.final_score)

        table.add_row(
            f"[bold]#{acct.rank}[/bold]",
            f"[bold]{acct.name}[/bold]",
            acct.region,
            ehr_display,
            f"[{color}]{acct.score_pct}[/{color}]",
            f"[{color}]{bar}[/{color}]",
            top_signal,
        )

    console.print(table)
    console.print()


def print_account_detail(acct: AccountScore):
    ehr_badge = f" ✓ [{acct.detected_ehr}]" if acct.ehr_confirmed else ""
    color = score_color(acct.score_pct)

    console.print(Panel(
        f"[bold white]#{acct.rank}  {acct.name}[/bold white]  [dim]{acct.region}[/dim]{ehr_badge}\n"
        f"[{color}]Score: {acct.score_pct}/100[/{color}]  "
        f"[dim]Raw: {acct.raw_score:.3f}  Final: {acct.final_score:.3f}"
        + (" (+EHR bonus)" if acct.ehr_confirmed else "") + "[/dim]",
        border_style=color if color != "white" else "dim",
        expand=False,
    ))

    # Signal breakdown table
    sig_table = Table(box=box.SIMPLE, show_header=True, header_style="bold", padding=(0, 1))
    sig_table.add_column("Signal", min_width=22)
    sig_table.add_column("Score", justify="center", width=8)
    sig_table.add_column("Weight", justify="center", width=8)
    sig_table.add_column("Contribution", justify="center", width=12)
    sig_table.add_column("Confidence", width=10)
    sig_table.add_column("Top Evidence", min_width=40)

    for sig_name in SIGNAL_WEIGHTS.keys():
        result = acct.signals.get(sig_name)
        if not result:
            continue
        weight = SIGNAL_WEIGHTS[sig_name]
        contrib = result.score * weight
        c = score_color(int(result.score * 100))
        evidence_preview = result.evidence[0][:80] + "…" if result.evidence else "[dim]none[/dim]"
        conf_color = "green" if result.confidence == "high" else "yellow" if result.confidence == "medium" else "dim"

        sig_table.add_row(
            sig_name.replace("_", " ").title(),
            f"[{c}]{result.score:.2f}[/{c}]",
            f"{weight:.2f}",
            f"[{c}]{contrib:.3f}[/{c}]",
            f"[{conf_color}]{result.confidence}[/{conf_color}]",
            evidence_preview,
        )

    console.print(sig_table)
    console.print()


def print_brief(brief_text: str, account_name: str):
    console.print(Panel(
        Markdown(brief_text),
        title=f"[bold cyan]Account Brief: {account_name}[/bold cyan]",
        border_style="cyan",
    ))
    console.print()


# ─────────────────────────────────────────────
# Output file writers
# ─────────────────────────────────────────────

def write_json_output(accounts: List[AccountScore], path: str):
    data = {
        "generated_at": datetime.now().isoformat(),
        "total_accounts": len(accounts),
        "accounts": [
            {
                "rank": a.rank,
                "name": a.name,
                "region": a.region,
                "score": round(a.final_score, 4),
                "score_pct": a.score_pct,
                "raw_score": round(a.raw_score, 4),
                "ehr_confirmed": a.ehr_confirmed,
                "detected_ehr": a.detected_ehr,
                "top_signals": a.top_signals[:4],
                "signals": a.signal_summary(),
                "notes": a.notes,
            }
            for a in accounts
        ],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def write_markdown_output(accounts: List[AccountScore], path: str):
    lines = [
        "# Solv Health Account Intelligence Report",
        f"\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n",
        "---\n",
        "## Ranked Accounts\n",
        "| Rank | Account | Region | EHR | Score | Top Signal |",
        "|------|---------|--------|-----|-------|------------|",
    ]
    for a in accounts:
        ehr = a.detected_ehr or "Unknown"
        top = a.top_signals[0].replace("_", " ").title() if a.top_signals else "-"
        lines.append(f"| #{a.rank} | {a.name} | {a.region} | {ehr} | {a.score_pct}/100 | {top} |")

    lines.append("\n---\n")
    lines.append("## Signal Detail\n")

    for a in accounts:
        lines.append(f"### #{a.rank} {a.name}\n")
        lines.append(f"**Region:** {a.region}  ")
        lines.append(f"**Score:** {a.score_pct}/100  ")
        lines.append(f"**EHR:** {a.detected_ehr or 'Unknown'}\n")

        if a.notes:
            lines.append(f"**Notes:** {a.notes}\n")

        lines.append("| Signal | Score | Weight | Evidence |")
        lines.append("|--------|-------|--------|----------|")
        for sig_name, result in a.signals.items():
            w = SIGNAL_WEIGHTS.get(sig_name, 0)
            ev = result.evidence[0][:100] if result.evidence else ""
            lines.append(f"| {sig_name.replace('_', ' ').title()} | {result.score:.2f} | {w:.2f} | {ev} |")
        lines.append("")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_brief_file(brief_text: str, account_name: str, briefs_dir: str):
    safe_name = account_name.lower().replace(" ", "_").replace("/", "_")
    path = Path(briefs_dir) / f"{safe_name}_brief.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Account Brief: {account_name}\n\n")
        f.write(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n---\n\n")
        f.write(brief_text)
    return str(path)


# ─────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────

def run_pipeline(
    companies: List[str],
    region: str,
    generate_briefs: bool,
    top_n: int,
    demo_mode: bool,
    companies_notes: Optional[dict] = None,
) -> List[AccountScore]:

    print_header()

    if demo_mode:
        console.print("[bold yellow]⚡ DEMO MODE[/bold yellow] - running with cached signal data (no API keys required)\n")
        from demo_data import DEMO_ACCOUNTS, DEMO_SIGNALS
        accounts_raw = DEMO_ACCOUNTS
    else:
        serpapi_key = os.environ.get("SERPAPI_KEY")
        if not serpapi_key:
            console.print("[red]Error: SERPAPI_KEY not set in environment. Use --demo for demo mode.[/red]")
            sys.exit(1)
        accounts_raw = [{"name": c, "region": region, "notes": ""} for c in companies]

    # ── Signal detection ──
    scored_accounts = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Detecting signals...", total=len(accounts_raw))

        for acct_info in accounts_raw:
            company = acct_info["name"]
            acct_region = acct_info.get("region", region)
            notes = acct_info.get("notes", "")
            progress.update(task, description=f"[cyan]Analyzing {company}...")

            if demo_mode:
                from demo_data import DEMO_SIGNALS
                signals = DEMO_SIGNALS.get(company, {})
            else:
                detector = SignalDetector(api_key=os.environ["SERPAPI_KEY"])
                signals = detector.detect_all(company, acct_region)

            scored = compute_score(company, acct_region, signals, notes)
            scored_accounts.append(scored)
            progress.advance(task)

    ranked = rank_accounts(scored_accounts)

    # ── Display results ──
    console.print(f"[bold]Analyzed {len(ranked)} accounts across region: [cyan]{region or 'multiple'}[/cyan][/bold]\n")
    print_ranked_table(ranked)

    for acct in ranked:
        print_account_detail(acct)

    # ── Write output files ──
    json_path = f"{OUTPUT_DIR}/accounts_ranked.json"
    md_path = f"{OUTPUT_DIR}/accounts_ranked.md"
    write_json_output(ranked, json_path)
    write_markdown_output(ranked, md_path)
    console.print(f"[dim]Output written to:[/dim]")
    console.print(f"  [green]{json_path}[/green]")
    console.print(f"  [green]{md_path}[/green]\n")

    # ── Brief generation ──
    if generate_briefs:
        if not demo_mode and not os.environ.get("ANTHROPIC_API_KEY"):
            console.print("[red]Error: ANTHROPIC_API_KEY not set. Cannot generate briefs.[/red]")
        else:
            top_accounts = ranked[:top_n]
            console.print(f"[bold cyan]Generating account briefs for top {len(top_accounts)} accounts...[/bold cyan]\n")

            from briefs import generate_brief

            if demo_mode:
                # In demo mode, still call Claude if key is set, else use stub
                anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            else:
                anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

            for acct in top_accounts:
                with console.status(f"[cyan]Writing brief for {acct.name}...[/cyan]"):
                    if anthropic_key:
                        brief = generate_brief(acct)
                    else:
                        brief = _demo_brief_stub(acct)

                print_brief(brief, acct.name)
                brief_path = write_brief_file(brief, acct.name, BRIEFS_DIR)
                console.print(f"[dim]Brief saved to:[/dim] [green]{brief_path}[/green]\n")

    return ranked


def _demo_brief_stub(acct: AccountScore) -> str:
    """Fallback brief when no ANTHROPIC_API_KEY is set in demo mode."""
    top_sig = acct.top_signals[0].replace("_", " ").title() if acct.top_signals else "Multiple signals"
    ehr = acct.detected_ehr or "Unknown EHR"

    # Collect top evidence snippets across all fired signals
    evidence_lines = []
    pain_lines = []
    for sig_name in acct.top_signals:
        result = acct.signals.get(sig_name)
        if result and result.score > 0.3 and result.evidence:
            evidence_lines.append(f"- **{sig_name.replace('_', ' ').title()}:** {result.evidence[0]}")
            if len(result.evidence) > 1:
                pain_lines.append(f"- {result.evidence[1]}")
        if len(evidence_lines) >= 4:
            break

    evidence_block = "\n".join(evidence_lines) if evidence_lines else "- Signal data not available"
    pain_block = "\n".join(pain_lines) if pain_lines else "- Front desk overload and intake friction consistent with Solv's ICP"

    # Build outreach using first real evidence snippet
    first_evidence = ""
    for sig_name in acct.top_signals[:3]:
        result = acct.signals.get(sig_name)
        if result and result.evidence:
            first_evidence = result.evidence[0]
            break

    return f"""## Company Snapshot
**{acct.name}** is a multi-site urgent care operator in {acct.region} running **{ehr}**.
Buying signal score: **{acct.score_pct}/100**.

## Why They're Likely to Buy Right Now
Top signal detected: **{top_sig}** - indicating active operational pain that Solv directly addresses.

{evidence_block}

## Pain Points Detected
{pain_block}

## Recommended Outreach Angle
Lead with the specific operational pain detected - don't pitch product features.
Reference what you found in reviews or job postings to establish credibility.

## Personalized Outreach Message

Subject: {acct.name} - noticed something about your front desk

Hi [Name],

I came across {acct.name} while researching urgent care operations in {acct.region} and noticed something worth flagging: {first_evidence}

That pattern - front desk teams absorbing workflow friction that their tools aren't handling - is exactly where we see Solv make the fastest impact. We integrate directly with {ehr} to automate inbound calls and patient check-in, which typically cuts the front desk load by 50-60%.

Worth a 20-minute conversation to see if the timing is right?

[Your name]
Solv Health

_Note: Set ANTHROPIC_API_KEY in .env to generate full AI-written briefs via Claude._"""


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Solv Health Account Intelligence - detect buying signals for urgent care operators",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo
  python main.py --demo --briefs
  python main.py --companies "MedRite Urgent Care,CityMD" --region "New York" --briefs
  python main.py --companies-file accounts.txt --region "Southeast" --top 5 --briefs
        """,
    )
    parser.add_argument(
        "--companies",
        type=str,
        help="Comma-separated list of company names to analyze",
    )
    parser.add_argument(
        "--companies-file",
        type=str,
        help="Path to a text file with one company name per line",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="",
        help="Geographic region to focus search (e.g. 'New York', 'Southeast')",
    )
    parser.add_argument(
        "--briefs",
        action="store_true",
        help="Generate AI-written account briefs for top accounts (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"Number of top accounts to generate briefs for (default: {DEFAULT_TOP_N})",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with cached signal data - no API keys required",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.demo and not args.companies and not args.companies_file:
        console.print("[red]Error:[/red] Provide --companies, --companies-file, or --demo\n")
        console.print("Quick start: [cyan]python main.py --demo --briefs[/cyan]")
        sys.exit(1)

    # Build company list
    companies = []
    if args.companies:
        companies = [c.strip() for c in args.companies.split(",") if c.strip()]
    elif args.companies_file:
        with open(args.companies_file) as f:
            companies = [line.strip() for line in f if line.strip()]

    region = args.region

    # In demo mode, region defaults to cover all 3 demo accounts
    if args.demo and not region:
        region = "Multi-region (NYC / Oklahoma / Texas / Southeast)"

    run_pipeline(
        companies=companies,
        region=region,
        generate_briefs=args.briefs,
        top_n=args.top,
        demo_mode=args.demo,
    )


if __name__ == "__main__":
    main()
