"""Smoke test: verifies the full init → review (which calls generate) cycle without real APIs."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


def _make_claude_side_effects():
    """Build a side_effect list for all Claude calls in the full cycle."""
    def msg(text):
        m = MagicMock()
        m.content = [MagicMock(text=text)]
        return m

    analysis = json.dumps({
        "voice": "Direct", "themes": ["AI"], "cadence": "2x/week",
        "gaps": [], "top_performers": [], "trend_context": "", "benchmark_context": ""
    })
    slot_24 = json.dumps([{"hook_type": "contrarian", "topic": f"T{i}"} for i in range(24)])
    return (
        [msg(analysis)]                           # init: analyze
        + [msg("W|||A|||C")]                      # init: build_strategy
        + [msg(slot_24)]                          # init: slot plan
        + [msg("Body.\nimage_query: AI")] * 24    # init: 24 posts
        + [msg("W2|||A2|||C2")]                   # review: update_strategy
        + [msg(slot_24)]                          # review→generate: slot plan
        + [msg("Body.\nimage_query: AI")] * 24    # review→generate: 24 posts
    )


def test_full_cycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: "3")  # rate all posts 3

    mock_claude = MagicMock()
    mock_claude.messages.create.side_effect = _make_claude_side_effects()

    mock_web = MagicMock()
    mock_web.fetch.return_value = "I build AI products."
    mock_web.search.return_value = "AI trends."
    mock_web.image_search.return_value = None

    sample_posts = [{"text": "AI is great.", "date": "2026-01-01", "likes": 10, "comments": 1}]

    state = str(tmp_path / "state")

    with patch("linkedin_agent.run._make_clients", return_value=(mock_claude, mock_web)), \
         patch("linkedin_agent.run.scrape_posts", return_value=sample_posts):
        from linkedin_agent.run import run_init, run_review
        run_init("https://ex.com", "https://linkedin.com/in/test", "AI PM", state)
        run_review(state_dir=state)

    s = Path(state)
    assert (s / "current-cycle.txt").read_text().strip() == "2"
    assert (s / "strategy-cycle-01.md").exists()
    assert len(list((s / "cycle-02").glob("week-*-post-*.md"))) == 24
