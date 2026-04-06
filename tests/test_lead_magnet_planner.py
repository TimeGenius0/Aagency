import json
import pytest
from unittest.mock import MagicMock, call
from lead_magnet_agent.planner import build_plan, _rank_ideas, _score_from_text


SAMPLE_BRIEF = {
    "profile_summary": "Senior marketing consultant specialising in AI automation.",
    "past_content": [],
    "web_findings": ["AI marketing tools trending in 2026"],
    "niche": "marketing consultant",
}


def _make_claude_brainstorm():
    """Returns a mock that gives valid brainstorm JSON then valid critic scores."""
    mock = MagicMock()
    ideas_json = json.dumps([
        {"title": "AI Marketing Audit Tool", "format": "app", "audience": "Marketing VPs",
         "angle": "Self-assessment scoring AI readiness", "core_promise": "Know your AI gap",
         "outline_seed": "10-question quiz with scored output", "impact": 8, "effort": 3},
        {"title": "2026 AI Marketing Benchmark Dataset", "format": "dataset", "audience": "Marketing directors",
         "angle": "Industry benchmarks for AI adoption", "core_promise": "See where you stand",
         "outline_seed": "50-row CSV + viz page", "impact": 7, "effort": 4},
        {"title": "AI Marketing Playbook", "format": "doc", "audience": "Marketing consultants",
         "angle": "Step-by-step guide to AI automation", "core_promise": "Automate 80% of reporting",
         "outline_seed": "6-section white paper", "impact": 7, "effort": 5},
    ])
    # First call = brainstorm, subsequent calls = critic (returns score >= 7 immediately)
    critic_response = "This is highly valuable and differentiated. Score: 8/10. Prospects would gladly exchange email."
    mock.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=ideas_json)]),
        MagicMock(content=[MagicMock(text=critic_response)]),
    ]
    return mock


def test_build_plan_returns_required_keys(tmp_path):
    plan = build_plan(
        brief=SAMPLE_BRIEF,
        state_dir=str(tmp_path),
        claude_client=_make_claude_brainstorm(),
        topic_hint=None,
    )
    for key in ("slug", "title", "format", "audience", "angle", "core_promise",
                "outline_seed", "impact_score", "effort_score", "why_it_wins", "critique_rounds"):
        assert key in plan, f"Missing key: {key}"


def test_build_plan_format_is_valid(tmp_path):
    plan = build_plan(
        brief=SAMPLE_BRIEF,
        state_dir=str(tmp_path),
        claude_client=_make_claude_brainstorm(),
        topic_hint=None,
    )
    assert plan["format"] in ("doc", "dataset", "app")


def test_build_plan_saves_plan_json_and_critique_log(tmp_path):
    build_plan(
        brief=SAMPLE_BRIEF,
        state_dir=str(tmp_path),
        claude_client=_make_claude_brainstorm(),
        topic_hint=None,
    )
    plans_dir = tmp_path / "plans"
    plan_files = list(plans_dir.glob("*-plan.json"))
    critique_files = list(plans_dir.glob("*-critique-log.md"))
    assert len(plan_files) == 1
    assert len(critique_files) == 1


def test_build_plan_critique_loop_exits_early_on_high_score(tmp_path):
    """Critic returns score >= 7 on round 1 — loop should exit after 1 critique call."""
    mock = _make_claude_brainstorm()
    plan = build_plan(
        brief=SAMPLE_BRIEF,
        state_dir=str(tmp_path),
        claude_client=mock,
        topic_hint=None,
    )
    # 1 brainstorm call + 1 critique call = 2 total
    assert mock.messages.create.call_count == 2
    assert plan["critique_rounds"] == 1


def test_build_plan_critique_loop_max_5_rounds(tmp_path):
    """Critic always returns score < 7 — loop should hit the 5-round cap."""
    mock = MagicMock()
    ideas_json = json.dumps([
        {"title": "Weak Idea", "format": "doc", "audience": "Anyone",
         "angle": "Generic", "core_promise": "Vague value",
         "outline_seed": "5 tips", "impact": 5, "effort": 5},
    ])
    low_score = "This is generic and won't drive downloads. Score: 4/10. Needs more specificity."
    refined_json = json.dumps([
        {"title": "Refined Weak Idea", "format": "doc", "audience": "Anyone",
         "angle": "Still generic", "core_promise": "Still vague",
         "outline_seed": "6 tips", "impact": 5, "effort": 5},
    ])
    # Pattern: brainstorm, critic(4), refine, critic(4), refine, critic(4), refine, critic(4), refine, critic(4)
    mock.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=ideas_json)]),
        MagicMock(content=[MagicMock(text=low_score)]),
        MagicMock(content=[MagicMock(text=refined_json)]),
        MagicMock(content=[MagicMock(text=low_score)]),
        MagicMock(content=[MagicMock(text=refined_json)]),
        MagicMock(content=[MagicMock(text=low_score)]),
        MagicMock(content=[MagicMock(text=refined_json)]),
        MagicMock(content=[MagicMock(text=low_score)]),
        MagicMock(content=[MagicMock(text=refined_json)]),
        MagicMock(content=[MagicMock(text=low_score)]),
    ]
    plan = build_plan(
        brief=SAMPLE_BRIEF,
        state_dir=str(tmp_path),
        claude_client=mock,
        topic_hint=None,
    )
    assert plan["critique_rounds"] == 5


def test_rank_ideas_picks_highest_impact_minus_half_effort():
    ideas = [
        {"title": "A", "format": "app", "impact": 8, "effort": 4},   # score = 6.0
        {"title": "B", "format": "doc", "impact": 9, "effort": 2},   # score = 8.0  <- winner
        {"title": "C", "format": "dataset", "impact": 7, "effort": 6},  # score = 4.0
    ]
    ranked = _rank_ideas(ideas)
    assert ranked[0]["title"] == "B"


def test_score_from_text_extracts_integer():
    assert _score_from_text("This scores 8/10 in my opinion.") == 8
    assert _score_from_text("Score: 3/10") == 3
    assert _score_from_text("no score here") == 5  # default
