# linkedin_agent/analyzer.py
"""Analyzes scraped LinkedIn posts to extract voice, themes, and benchmarks."""
from __future__ import annotations
import json


def analyze_posts(
    posts: list[dict],
    niche: str,
    claude_client,
    web_client,
) -> dict:
    """
    Analyze posts and return a dict with voice, themes, cadence, gaps,
    top_performers, trend_context, benchmark_context.
    """
    trend_context = web_client.search(f"{niche} LinkedIn trends") or ""
    benchmark_context = web_client.search(f"top LinkedIn influencers {niche}") or ""

    posts_text = "\n\n---\n\n".join(
        f"Date: {p.get('date','')}\nLikes: {p.get('likes',0)}\nComments: {p.get('comments',0)}\n\n{p['text']}"
        for p in posts
    )

    system = (
        "You are a LinkedIn content strategist. "
        "Analyze the provided posts and return JSON only — no prose."
    )
    user = f"""Analyze these LinkedIn posts for a {niche} professional.

POSTS:
{posts_text}

INDUSTRY TRENDS:
{trend_context}

TOP INFLUENCER BENCHMARKS:
{benchmark_context}

Return a JSON object with these exact keys:
- voice: string describing writing style and tone
- themes: list of strings (recurring content topics, most frequent first)
- cadence: string describing posting frequency
- gaps: list of strings (content types they haven't tried but should)
- top_performers: list of strings (first 100 chars of 3 highest-engagement posts)
- trend_context: string (2-3 sentence summary of industry trends)
- benchmark_context: string (2-3 sentence summary of influencer benchmarks)
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
