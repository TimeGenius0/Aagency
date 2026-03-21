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


def test_generate_advances_cycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    (state / "current-cycle.txt").write_text("1")
    (state / "niche.txt").write_text("AI product management")
    (state / "strategy.md").write_text(
        "# Strategy\n## Content Mix\n- 40% contrarian\n- 30% behind-the-scenes\n- 20% how-to\n- 10% story\n"
    )

    slot_plan = json.dumps([{"hook_type": "contrarian", "topic": f"T{i}"} for i in range(24)])
    mock_anthropic = MagicMock()
    mock_anthropic.messages.create.side_effect = (
        [_make_msg(slot_plan)]
        + [_make_msg("Post body.\nimage_query: AI")] * 24
    )

    mock_web = MagicMock()
    mock_web.search.return_value = "trends"
    mock_web.image_search.return_value = None

    with patch("linkedin_agent.run._make_clients", return_value=(mock_anthropic, mock_web)):
        from linkedin_agent.run import run_generate
        run_generate(state_dir=str(state))

    assert (state / "current-cycle.txt").read_text().strip() == "2"
    assert (state / "cycle-02").exists()
    assert len(list((state / "cycle-02").glob("week-*-post-*.md"))) == 24


def test_review_archives_strategy_and_calls_generate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    (state / "current-cycle.txt").write_text("1")
    (state / "niche.txt").write_text("AI product management")
    (state / "strategy.md").write_text(
        "# Content Strategy — Cycle 1\n"
        "## Voice & Tone\nDirect\n"
        "## Core Themes (ranked by past performance)\n1. AI\n"
        "## Content Mix\n- 40% contrarian\n- 30% behind-the-scenes\n- 20% how-to\n- 10% story\n"
    )
    cycle_dir = state / "cycle-01"
    cycle_dir.mkdir()
    for i in range(1, 3):
        (cycle_dir / f"week-01-post-{i}.md").write_text(
            f"---\nweek: 1\npost: {i}\ntopic: AI\nhook_type: contrarian\n"
            f"status: draft\npublished_text_snippet: \"\"\npublished_url: \"\"\n"
            f"image_url: null\nimage_credit: null\nimage_query: \"AI\"\n---\n\nPost body."
        )

    slot_plan = json.dumps([{"hook_type": "contrarian", "topic": f"T{i}"} for i in range(24)])
    mock_anthropic = MagicMock()
    mock_anthropic.messages.create.side_effect = (
        [_make_msg("Working|||Avoid|||Context")]   # update_strategy
        + [_make_msg(slot_plan)]                   # slot plan
        + [_make_msg("Post body.\nimage_query: AI")] * 24
    )

    mock_web = MagicMock()
    mock_web.search.return_value = "trends"
    mock_web.image_search.return_value = None

    monkeypatch.setattr("builtins.input", lambda _: "3")

    with patch("linkedin_agent.run._make_clients", return_value=(mock_anthropic, mock_web)), \
         patch("linkedin_agent.run.scrape_posts", return_value=[]):
        from linkedin_agent.run import run_review
        run_review(state_dir=str(state))

    assert (state / "strategy-cycle-01.md").exists()
    assert (state / "current-cycle.txt").read_text().strip() == "2"
