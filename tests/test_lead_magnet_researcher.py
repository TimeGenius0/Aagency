from lead_magnet_agent.web import WebClient


def test_webclient_importable():
    assert WebClient is not None


import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from lead_magnet_agent.researcher import build_research_brief


def _make_claude(summary: str = "Expert marketing consultant focused on AI."):
    mock = MagicMock()
    mock.messages.create.return_value = MagicMock(
        content=[MagicMock(text=summary)]
    )
    return mock


def _make_web(search_result: str = "AI marketing trends 2026"):
    mock = MagicMock()
    mock.fetch.return_value = "Landing page text about marketing consulting."
    mock.search.return_value = search_result
    return mock


def test_build_research_brief_returns_required_keys(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "content").mkdir()

    brief = build_research_brief(
        url="https://example.com",
        niche="marketing consultant",
        state_dir=str(state_dir),
        claude_client=_make_claude(),
        web_client=_make_web(),
    )

    assert "profile_summary" in brief
    assert "past_content" in brief
    assert "web_findings" in brief
    assert "niche" in brief
    assert brief["niche"] == "marketing consultant"


def test_build_research_brief_reads_past_content(tmp_path):
    state_dir = tmp_path / "state"
    content_dir = state_dir / "content" / "ai-guide"
    content_dir.mkdir(parents=True)
    (content_dir / "meta.json").write_text(json.dumps({
        "title": "AI Guide", "format": "doc", "date": "2025-01-01", "topic": "AI"
    }))
    (content_dir / "impact.json").write_text(json.dumps({
        "downloads": 120, "leads_generated": 45, "notes": "Performed well"
    }))

    brief = build_research_brief(
        url="https://example.com",
        niche="marketing consultant",
        state_dir=str(state_dir),
        claude_client=_make_claude(),
        web_client=_make_web(),
    )

    assert len(brief["past_content"]) == 1
    assert brief["past_content"][0]["meta"]["title"] == "AI Guide"
    assert brief["past_content"][0]["impact"]["downloads"] == 120


def test_build_research_brief_handles_missing_content_dir(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    # No content/ subdir

    brief = build_research_brief(
        url="https://example.com",
        niche="marketing consultant",
        state_dir=str(state_dir),
        claude_client=_make_claude(),
        web_client=_make_web(),
    )

    assert brief["past_content"] == []


def test_build_research_brief_handles_web_failure(tmp_path):
    state_dir = tmp_path / "state"
    (state_dir / "content").mkdir(parents=True)

    web = _make_web()
    web.search.return_value = None  # web failed

    brief = build_research_brief(
        url="https://example.com",
        niche="marketing consultant",
        state_dir=str(state_dir),
        claude_client=_make_claude(),
        web_client=web,
    )

    # Should still return a brief with empty or partial web_findings
    assert isinstance(brief["web_findings"], list)
