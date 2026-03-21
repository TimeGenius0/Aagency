import json
from unittest.mock import MagicMock
from linkedin_agent.strategist import build_strategy, update_strategy

SAMPLE_ANALYSIS = {
    "voice": "Direct and technical",
    "themes": ["AI agents", "product management"],
    "cadence": "2 posts/week",
    "gaps": ["personal stories"],
    "top_performers": ["AI is transforming PM."],
    "trend_context": "AI agents trending",
    "benchmark_context": "Top influencers post 3x/week"
}


def test_build_strategy_writes_file(tmp_path):
    mock_claude = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="# Content Strategy — Cycle 1\nGenerated: 2026-03-20\n\n## Voice & Tone\nDirect.")]
    mock_claude.messages.create.return_value = mock_msg

    state_dir = tmp_path / "state"
    state_dir.mkdir()

    build_strategy(
        landing_text="I help companies build AI products.",
        analysis=SAMPLE_ANALYSIS,
        niche="AI product management",
        state_dir=str(state_dir),
        cycle=1,
        claude_client=mock_claude,
    )
    strategy = (state_dir / "strategy.md").read_text()
    assert "Content Strategy" in strategy


def test_update_strategy_archives_old(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "strategy.md").write_text("# Content Strategy — Cycle 1\n## Voice & Tone\nDirect\n## Core Themes (ranked by past performance)\n1. AI\n")

    mock_claude = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Working well|||Things to avoid|||Current trends")]
    mock_claude.messages.create.return_value = mock_msg

    review_md = "## What Worked\nAI posts did well."

    update_strategy(
        review_md=review_md,
        niche="AI product management",
        state_dir=str(state_dir),
        cycle=1,
        claude_client=mock_claude,
    )
    assert (state_dir / "strategy-cycle-01.md").exists()
    assert "Cycle 2" in (state_dir / "strategy.md").read_text()
