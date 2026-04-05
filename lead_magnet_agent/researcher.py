# lead_magnet_agent/researcher.py
"""Research phase: fetch consultant profile, search web, read past content."""
from __future__ import annotations
import json
from pathlib import Path


_SEARCH_QUERIES = [
    "{niche} trends 2026",
    "{niche} lead magnet ideas",
    "{niche} audience pain points",
    "best lead magnets for {niche} consultants",
    "{niche} competitor resources",
]


def build_research_brief(
    url: str,
    niche: str,
    state_dir: str,
    claude_client,
    web_client,
) -> dict:
    """
    Returns a research_brief dict:
    {
      "profile_summary": str,
      "past_content": [{"meta": dict, "impact": dict}, ...],
      "web_findings": [str, ...],
      "niche": str,
    }
    """
    # 1. Fetch and summarise the landing page
    page_text = web_client.fetch(url) or ""
    profile_summary = _extract_profile(page_text, niche, claude_client)

    # 2. Read past content from state/content/
    past_content = _read_past_content(state_dir)

    # 3. Web searches
    web_findings = _search_web(niche, web_client)

    return {
        "profile_summary": profile_summary,
        "past_content": past_content,
        "web_findings": web_findings,
        "niche": niche,
    }


def _extract_profile(page_text: str, niche: str, claude_client) -> str:
    prompt = f"""Extract a concise consultant profile from this landing page text.
Include: name (if present), positioning, target audience, and areas of expertise.
Keep it under 150 words. Return plain text only.

LANDING PAGE:
{page_text[:3000]}
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _read_past_content(state_dir: str) -> list[dict]:
    content_dir = Path(state_dir) / "content"
    if not content_dir.exists():
        return []

    results = []
    for slug_dir in sorted(content_dir.iterdir()):
        if not slug_dir.is_dir():
            continue
        meta_path = slug_dir / "meta.json"
        impact_path = slug_dir / "impact.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        impact = json.loads(impact_path.read_text()) if impact_path.exists() else {}
        results.append({"slug": slug_dir.name, "meta": meta, "impact": impact})
    return results


def _search_web(niche: str, web_client) -> list[str]:
    queries = [q.format(niche=niche) for q in _SEARCH_QUERIES]
    findings = []
    for query in queries:
        result = web_client.search(query)
        if result:
            findings.append(result)
    return findings
