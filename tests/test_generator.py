import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from linkedin_agent.generator import build_slot_plan, generate_posts

SAMPLE_STRATEGY = """# Content Strategy — Cycle 1
Generated: 2026-03-20

## Content Mix (per 8-week cycle)
- 40% thought leadership (contrarian takes)
- 30% behind-the-scenes / build-in-public
- 20% tactical how-tos
- 10% personal story
"""


def test_build_slot_plan_returns_24_slots():
    mock_claude = MagicMock()
    slots_data = [
        {"hook_type": "contrarian", "topic": f"Topic {i}"}
        for i in range(24)
    ]
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(slots_data))]
    mock_claude.messages.create.return_value = mock_msg

    slots = build_slot_plan(
        strategy_md=SAMPLE_STRATEGY,
        niche="AI product management",
        claude_client=mock_claude,
        web_client=MagicMock(search=lambda q: "trends"),
    )
    assert len(slots) == 24
    assert all("week" in s and "position" in s for s in slots)
    assert slots[0]["week"] == 1
    assert slots[2]["week"] == 1   # 3 posts per week
    assert slots[3]["week"] == 2


def test_generate_posts_writes_files(tmp_path):
    mock_claude = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Here is the post content.\n\nimage_query: AI office")]
    mock_claude.messages.create.return_value = mock_msg

    mock_web = MagicMock()
    mock_web.search.return_value = "Latest AI news."
    mock_web.image_search.return_value = {
        "url": "https://unsplash.com/photo.jpg",
        "source_domain": "unsplash.com",
        "photographer": "Jane Doe",
    }

    slots = [
        {"week": 1, "position": 1, "hook_type": "contrarian", "topic": "AI replacing PMs"},
        {"week": 1, "position": 2, "hook_type": "how-to", "topic": "Build an AI agent"},
    ]
    voice_posts = [{"text": "Example voice post."}]

    generate_posts(
        cycle_dir=str(tmp_path),
        slots=slots,
        strategy_md=SAMPLE_STRATEGY,
        voice_posts=voice_posts,
        claude_client=mock_claude,
        web_client=mock_web,
    )
    assert (tmp_path / "week-01-post-1.md").exists()
    assert (tmp_path / "week-01-post-2.md").exists()
    content = (tmp_path / "week-01-post-1.md").read_text()
    assert "status: draft" in content


def test_generate_posts_resumes_interrupted(tmp_path):
    """Posts that already exist should not be regenerated."""
    existing = tmp_path / "week-01-post-1.md"
    existing.write_text("---\nweek: 1\npost: 1\nstatus: draft\n---\nExisting content")

    mock_claude = MagicMock()
    mock_web = MagicMock()

    slots = [{"week": 1, "position": 1, "hook_type": "contrarian", "topic": "AI"}]
    generate_posts(
        cycle_dir=str(tmp_path),
        slots=slots,
        strategy_md=SAMPLE_STRATEGY,
        voice_posts=[],
        claude_client=mock_claude,
        web_client=mock_web,
    )
    # Claude should not have been called — post already exists
    mock_claude.messages.create.assert_not_called()


def test_generate_posts_all_24_weeks(tmp_path):
    """All 24 posts across 8 weeks are generated with correct filenames."""
    mock_claude = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Post body.\nimage_query: AI office")]
    mock_claude.messages.create.return_value = mock_msg

    mock_web = MagicMock()
    mock_web.search.return_value = "news"
    mock_web.image_search.return_value = None

    slots = [
        {"week": w, "position": p, "hook_type": "contrarian", "topic": f"Topic w{w}p{p}"}
        for w in range(1, 9) for p in range(1, 4)
    ]
    assert len(slots) == 24

    generate_posts(
        cycle_dir=str(tmp_path),
        slots=slots,
        strategy_md=SAMPLE_STRATEGY,
        voice_posts=[],
        claude_client=mock_claude,
        web_client=mock_web,
    )
    files = list(tmp_path.glob("week-*-post-*.md"))
    assert len(files) == 24
    assert (tmp_path / "week-08-post-3.md").exists()
