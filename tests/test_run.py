import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


def _make_msg(text):
    m = MagicMock()
    m.content = [MagicMock(text=text)]
    return m


def test_init_creates_state_structure(tmp_path, monkeypatch):
    """init mode creates state/, writes current-cycle.txt=1, niche.txt, linkedin-url.txt, generates 24 posts."""
    monkeypatch.chdir(tmp_path)

    analysis_result = json.dumps({
        "voice": "Direct", "themes": ["AI"], "cadence": "2x/week",
        "gaps": [], "top_performers": [], "trend_context": "", "benchmark_context": ""
    })
    slot_plan = json.dumps([
        {"hook_type": "contrarian", "topic": f"Topic {i}"} for i in range(24)
    ])
    mock_anthropic = MagicMock()
    mock_anthropic.messages.create.side_effect = (
        [_make_msg(analysis_result)]             # analyzer
        + [_make_msg("Working|||Avoid|||Context")]  # strategist
        + [_make_msg(slot_plan)]                 # slot plan
        + [_make_msg("Post body.\nimage_query: AI")] * 24  # 24 posts
    )

    mock_web = MagicMock()
    mock_web.fetch.return_value = "I help build AI products."
    mock_web.search.return_value = "AI trends."
    mock_web.image_search.return_value = None

    mock_scraper_posts = [{"text": "Sample post.", "date": "2026-01-01", "likes": 10, "comments": 1}]

    with patch("linkedin_agent.run._make_clients", return_value=(mock_anthropic, mock_web)), \
         patch("linkedin_agent.run.scrape_posts", return_value=mock_scraper_posts):
        from linkedin_agent.run import run_init
        run_init(
            landing_page_url="https://example.com",
            linkedin_url="https://linkedin.com/in/test",
            niche="AI product management",
            state_dir=str(tmp_path / "state"),
        )

    state = tmp_path / "state"
    assert (state / "current-cycle.txt").read_text().strip() == "1"
    assert (state / "niche.txt").read_text().strip() == "AI product management"
    assert (state / "linkedin-url.txt").read_text().strip() == "https://linkedin.com/in/test"
    assert (state / "strategy.md").exists()
    assert (state / "cycle-01" / "slot-plan.json").exists()
    assert len(list((state / "cycle-01").glob("week-*-post-*.md"))) == 24
