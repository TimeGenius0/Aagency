# linkedin_agent/strategist.py
"""Builds and updates content strategy from analysis and review data."""
from __future__ import annotations
import datetime
import re
from pathlib import Path


_STRATEGY_TEMPLATE = """# Content Strategy — Cycle {cycle}
Generated: {today} | Next review: {next_review}

## Voice & Tone
{voice}

## Core Themes (ranked by past performance)
{themes}

## Content Mix (per 8-week cycle)
- 40% thought leadership (contrarian takes)
- 30% behind-the-scenes / build-in-public
- 20% tactical how-tos
- 10% personal story

## Posting Cadence
3× per week — Mon / Wed / Fri

## What's Working
{whats_working}

## What to Avoid
{what_to_avoid}

## Industry Context
{industry_context}
"""


def build_strategy(
    landing_text: str,
    analysis: dict,
    niche: str,
    state_dir: str,
    cycle: int,
    claude_client,
) -> None:
    """Generate strategy.md from landing page + analysis. Overwrites any existing file."""
    today = datetime.date.today().isoformat()
    next_review = (datetime.date.today() + datetime.timedelta(days=56)).isoformat()

    themes_str = "\n".join(
        f"{i+1}. {t}" for i, t in enumerate(analysis.get("themes", []))
    )

    user = f"""You are a LinkedIn content strategist for a {niche} professional.

LANDING PAGE:
{landing_text[:2000]}

VOICE ANALYSIS: {analysis.get('voice', '')}
THEMES: {', '.join(analysis.get('themes', []))}
CONTENT GAPS: {', '.join(analysis.get('gaps', []))}
INDUSTRY TRENDS: {analysis.get('trend_context', '')}
BENCHMARKS: {analysis.get('benchmark_context', '')}

Write the "What's Working", "What to Avoid", and "Industry Context" sections for a cycle 1 strategy.
- What's Working: empty for cycle 1 (no engagement data yet). Write: "[No data yet — cycle 1]"
- What to Avoid: based on gaps analysis. 2-3 bullets.
- Industry Context: 3-4 sentences summarizing trends and benchmarks. Max 120 words.

Return only these three sections as plain text, separated by "|||".
Format: <whats_working>|||<what_to_avoid>|||<industry_context>
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": user}],
    )
    parts = response.content[0].text.strip().split("|||")
    whats_working = parts[0].strip() if len(parts) > 0 else "[No data yet — cycle 1]"
    what_to_avoid = parts[1].strip() if len(parts) > 1 else ""
    industry_context = parts[2].strip() if len(parts) > 2 else analysis.get("trend_context", "")

    strategy = _STRATEGY_TEMPLATE.format(
        cycle=cycle,
        today=today,
        next_review=next_review,
        voice=analysis.get("voice", ""),
        themes=themes_str,
        whats_working=whats_working,
        what_to_avoid=what_to_avoid,
        industry_context=industry_context,
    )
    Path(state_dir, "strategy.md").write_text(strategy)


def update_strategy(
    review_md: str,
    niche: str,
    state_dir: str,
    cycle: int,
    claude_client,
) -> None:
    """
    Archive current strategy.md to strategy-cycle-{N}.md,
    then generate a new strategy.md using review data.
    """
    state = Path(state_dir)
    current = state / "strategy.md"
    old_text = current.read_text() if current.exists() else ""

    # Archive old strategy
    archive_name = f"strategy-cycle-{cycle:02d}.md"
    (state / archive_name).write_text(old_text)

    today = datetime.date.today().isoformat()
    next_review = (datetime.date.today() + datetime.timedelta(days=56)).isoformat()

    user = f"""You are a LinkedIn content strategist for a {niche} professional.

CURRENT STRATEGY:
{old_text[:2000]}

REVIEW DATA (engagement + ratings from last 8 weeks):
{review_md[:1500]}

Update the strategy for cycle {cycle + 1}. Write these three sections only, separated by "|||":
1. What's Working: bullet points of what drove high ratings/engagement
2. What to Avoid: bullet points of what to drop or reduce
3. Industry Context: 3-4 sentences of updated trends for the next cycle

Format: <whats_working>|||<what_to_avoid>|||<industry_context>
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": user}],
    )
    try:
        parts = response.content[0].text.strip().split("|||")
        if len(parts) < 3:
            raise ValueError(f"Expected 3 sections separated by '|||', got {len(parts)}")
        whats_working = parts[0].strip()
        what_to_avoid = parts[1].strip()
        industry_context = parts[2].strip()
    except (ValueError, IndexError) as e:
        print(f"WARNING: Could not parse strategy update sections: {e}. Using placeholders.")
        whats_working = "[Review review.md manually — parsing failed]"
        what_to_avoid = "[Review review.md manually — parsing failed]"
        industry_context = "[Update manually]"

    # Build new strategy — preserve themes/voice from old, update working/avoid/context
    voice_match = re.search(r"## Voice & Tone\n(.+?)(?=\n##)", old_text, re.DOTALL)
    if voice_match:
        voice = voice_match.group(1).strip()
    else:
        print("WARNING: Could not parse Voice & Tone from old strategy. Using placeholder.")
        voice = "[Review strategy.md — Voice & Tone section not found]"

    themes_match = re.search(r"## Core Themes.*?\n(.+?)(?=\n##)", old_text, re.DOTALL)
    if themes_match:
        themes = themes_match.group(1).strip()
    else:
        print("WARNING: Could not parse Core Themes from old strategy. Using placeholder.")
        themes = "[Review strategy.md — Core Themes section not found]"

    strategy = _STRATEGY_TEMPLATE.format(
        cycle=cycle + 1,
        today=today,
        next_review=next_review,
        voice=voice,
        themes=themes,
        whats_working=whats_working,
        what_to_avoid=what_to_avoid,
        industry_context=industry_context,
    )
    current.write_text(strategy)
