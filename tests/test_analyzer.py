import json
import pytest
from unittest.mock import MagicMock
from linkedin_agent.analyzer import analyze_posts

SAMPLE_POSTS = [
    {"text": "AI is transforming product management.", "date": "2026-01-01", "likes": 50, "comments": 5},
    {"text": "Here's how I built an AI agent in 3 hours.", "date": "2026-01-08", "likes": 30, "comments": 2},
]


def test_analyze_posts_returns_expected_keys(mocker):
    mock_anthropic = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        "voice": "Direct and technical",
        "themes": ["AI agents", "product management"],
        "cadence": "~2 posts/week",
        "gaps": ["personal stories"],
        "top_performers": ["AI is transforming product management."],
        "trend_context": "AI agents are trending in 2026",
        "benchmark_context": "Top influencers post 3x/week"
    }))]
    mock_anthropic.messages.create.return_value = mock_message

    mock_web = MagicMock()
    mock_web.search.return_value = "AI agents trending 2026"

    result = analyze_posts(
        posts=SAMPLE_POSTS,
        niche="AI product management",
        claude_client=mock_anthropic,
        web_client=mock_web,
    )
    assert "voice" in result
    assert "themes" in result
    assert isinstance(result["themes"], list)


def test_analyze_posts_handles_web_failure(mocker):
    mock_anthropic = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        "voice": "Direct", "themes": [], "cadence": "", "gaps": [],
        "top_performers": [], "trend_context": "", "benchmark_context": ""
    }))]
    mock_anthropic.messages.create.return_value = mock_message

    mock_web = MagicMock()
    mock_web.search.return_value = None  # web failed

    result = analyze_posts(
        posts=SAMPLE_POSTS,
        niche="AI product management",
        claude_client=mock_anthropic,
        web_client=mock_web,
    )
    assert result is not None  # should proceed without web context


def test_analyze_posts_raises_on_malformed_json():
    """Malformed Claude response (not JSON) should raise JSONDecodeError."""
    import json as _json
    mock_anthropic = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Sorry, I cannot analyze this content.")]
    mock_anthropic.messages.create.return_value = mock_message

    mock_web = MagicMock()
    mock_web.search.return_value = None

    with pytest.raises(_json.JSONDecodeError):
        analyze_posts(
            posts=SAMPLE_POSTS,
            niche="AI product management",
            claude_client=mock_anthropic,
            web_client=mock_web,
        )
