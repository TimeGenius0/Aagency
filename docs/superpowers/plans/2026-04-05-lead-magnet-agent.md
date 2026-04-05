# Lead Magnet Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI agent (`lead-magnet-agent`) that takes a consultant's landing page URL, researches their niche, brainstorms and critiques lead magnet ideas across doc/dataset/app formats, surfaces the best for approval, then generates the final artifact.

**Architecture:** Modular pipeline mirroring `linkedin_agent/` — `run.py` orchestrates three modes (`init`, `plan`, `generate`), each backed by focused modules (`researcher.py`, `planner.py`, `writer.py`). State lives on disk between modes. The approval checkpoint is enforced by the CLI: `generate` only runs after an approved `plan.json` exists.

**Tech Stack:** Python 3.11+, `anthropic` (claude-sonnet-4-6), `openclaw` (web search via `linkedin_agent.web.WebClient`), `beautifulsoup4`, `httpx`, `pytest`, `pytest-mock`

---

## File Map

| File | Responsibility |
|---|---|
| `lead_magnet_agent/__init__.py` | Package marker |
| `lead_magnet_agent/web.py` | Re-export `WebClient` from `linkedin_agent.web` |
| `lead_magnet_agent/researcher.py` | Fetch URL, search web, read past content state → `research_brief` dict |
| `lead_magnet_agent/planner.py` | Brainstorm ideas, score impact/effort, run critique loop (max 5), return plan |
| `lead_magnet_agent/writer.py` | Format-aware artifact generator: `doc`, `dataset`, `app` |
| `lead_magnet_agent/run.py` | CLI orchestrator: `init`, `plan`, `generate` |
| `tests/test_lead_magnet_researcher.py` | Unit tests for researcher |
| `tests/test_lead_magnet_planner.py` | Unit tests for planner |
| `tests/test_lead_magnet_writer.py` | Unit tests for writer |
| `tests/test_lead_magnet_run.py` | Integration tests for CLI modes |

---

## Task 1: Package scaffold + web.py re-export

**Files:**
- Create: `lead_magnet_agent/__init__.py`
- Create: `lead_magnet_agent/web.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lead_magnet_researcher.py  (create file now, add to it in Task 2)
from lead_magnet_agent.web import WebClient

def test_webclient_importable():
    assert WebClient is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/bilelburaway/dev/Aagency
pytest tests/test_lead_magnet_researcher.py::test_webclient_importable -v
```

Expected: `ModuleNotFoundError: No module named 'lead_magnet_agent'`

- [ ] **Step 3: Create `lead_magnet_agent/__init__.py`**

```python
# lead_magnet_agent/__init__.py
```

(empty file)

- [ ] **Step 4: Create `lead_magnet_agent/web.py`**

```python
# lead_magnet_agent/web.py
"""Re-export WebClient from linkedin_agent for use within lead_magnet_agent."""
from linkedin_agent.web import WebClient

__all__ = ["WebClient"]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_lead_magnet_researcher.py::test_webclient_importable -v
```

Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add lead_magnet_agent/__init__.py lead_magnet_agent/web.py tests/test_lead_magnet_researcher.py
git commit -m "feat(lead-magnet): scaffold package and web.py re-export"
```

---

## Task 2: `researcher.py` — fetch profile + web search + read past content

**Files:**
- Create: `lead_magnet_agent/researcher.py`
- Modify: `tests/test_lead_magnet_researcher.py`

The researcher produces a `research_brief` dict:
```python
{
  "profile_summary": str,   # Claude-extracted from landing page text
  "past_content": list,     # from state/content/*/meta.json + impact.json
  "web_findings": list,     # 3-5 search result strings
  "niche": str
}
```

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_lead_magnet_researcher.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_lead_magnet_researcher.py -v
```

Expected: `ImportError: cannot import name 'build_research_brief'`

- [ ] **Step 3: Implement `researcher.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_lead_magnet_researcher.py -v
```

Expected: all 5 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add lead_magnet_agent/researcher.py tests/test_lead_magnet_researcher.py
git commit -m "feat(lead-magnet): add researcher.py with profile extraction and web search"
```

---

## Task 3: `planner.py` — brainstorm, score, critique loop, output plan

**Files:**
- Create: `lead_magnet_agent/planner.py`
- Create: `tests/test_lead_magnet_planner.py`

The planner outputs a `plan` dict:
```python
{
  "slug": str,           # kebab-case title
  "title": str,
  "format": str,         # "doc" | "dataset" | "app"
  "audience": str,
  "angle": str,
  "core_promise": str,
  "outline_seed": str,   # high-level description for writer
  "impact_score": int,
  "effort_score": int,
  "why_it_wins": str,
  "critique_rounds": int,
}
```

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_lead_magnet_planner.py
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
    # First call = brainstorm, subsequent calls = critic (returns score ≥ 7 immediately)
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
    """Critic returns score ≥ 7 on round 1 — loop should exit after 1 critique call."""
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
        {"title": "B", "format": "doc", "impact": 9, "effort": 2},   # score = 8.0  ← winner
        {"title": "C", "format": "dataset", "impact": 7, "effort": 6},  # score = 4.0
    ]
    ranked = _rank_ideas(ideas)
    assert ranked[0]["title"] == "B"


def test_score_from_text_extracts_integer():
    assert _score_from_text("This scores 8/10 in my opinion.") == 8
    assert _score_from_text("Score: 3/10") == 3
    assert _score_from_text("no score here") == 5  # default
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_lead_magnet_planner.py -v
```

Expected: `ImportError: cannot import name 'build_plan'`

- [ ] **Step 3: Implement `planner.py`**

```python
# lead_magnet_agent/planner.py
"""Planning phase: brainstorm ideas, score, critique loop, output plan."""
from __future__ import annotations
import json
import re
import datetime
from pathlib import Path


_MAX_CRITIQUE_ROUNDS = 5
_PASS_THRESHOLD = 7


def build_plan(
    brief: dict,
    state_dir: str,
    claude_client,
    topic_hint: str | None = None,
) -> dict:
    """
    Brainstorm → score → critique loop → return winning plan dict.
    Also saves <slug>-plan.json and <slug>-critique-log.md to state_dir/plans/.
    """
    niche = brief["niche"]
    ideas = _brainstorm(brief, topic_hint, claude_client)
    ranked = _rank_ideas(ideas)
    top = ranked[0]

    critique_log = []
    best = top
    best_score = 0

    for round_num in range(1, _MAX_CRITIQUE_ROUNDS + 1):
        score, rationale = _critique(best, niche, brief, claude_client)
        critique_log.append({
            "round": round_num,
            "title": best["title"],
            "score": score,
            "rationale": rationale,
        })
        if score > best_score:
            best_score = score
            best_plan = dict(best)
            best_plan["why_it_wins"] = rationale
            best_plan["critique_rounds"] = round_num

        if score >= _PASS_THRESHOLD:
            break

        if round_num < _MAX_CRITIQUE_ROUNDS:
            best = _refine(best, rationale, niche, brief, claude_client)

    plan = _make_plan_dict(best_plan, niche)
    _save_plan(plan, critique_log, state_dir)
    return plan


def _brainstorm(brief: dict, topic_hint: str | None, claude_client) -> list[dict]:
    niche = brief["niche"]
    past_summary = _summarise_past(brief["past_content"])
    web_summary = "\n".join(brief["web_findings"][:3])

    hint_line = f"\nFocus especially on this topic area: {topic_hint}" if topic_hint else ""

    prompt = f"""You are a lead magnet strategist for senior {niche} consultants.

CONSULTANT PROFILE:
{brief["profile_summary"]}

PAST LEAD MAGNETS AND THEIR IMPACT:
{past_summary}

WEB RESEARCH FINDINGS:
{web_summary}
{hint_line}

Brainstorm 6-9 lead magnet ideas for this consultant's audience.
Spread ideas across all three formats: doc (white paper/guide), dataset, app (interactive HTML/JS tool).

For each idea return a JSON object with these exact keys:
- title: string
- format: "doc" | "dataset" | "app"
- audience: string (who downloads this)
- angle: string (the specific hook/angle)
- core_promise: string (what the reader gets)
- outline_seed: string (1-2 sentences on structure/content)
- impact: integer 1-10 (audience fit, uniqueness, download pull)
- effort: integer 1-10 (complexity to produce — lower = easier)

Return a JSON array only. No prose.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"```\w*\n?", "", raw).strip().rstrip("```").strip()
    return json.loads(raw)


def _rank_ideas(ideas: list[dict]) -> list[dict]:
    """Sort by impact - effort*0.5, descending. Return sorted list."""
    return sorted(ideas, key=lambda x: x["impact"] - x["effort"] * 0.5, reverse=True)


def _critique(idea: dict, niche: str, brief: dict, claude_client) -> tuple[int, str]:
    prompt = f"""You are a harsh but fair critic of lead magnets for {niche} consultants.

PROPOSED LEAD MAGNET:
Title: {idea["title"]}
Format: {idea["format"]}
Audience: {idea["audience"]}
Angle: {idea["angle"]}
Core Promise: {idea["core_promise"]}

Would a senior {niche} consultant's prospect pay with their email address to download this?
Score it 1-10 (10 = definitely yes, 1 = definitely not).
Explain specifically why they would or would not download it.
Be concrete about what makes it compelling or generic.

End your response with exactly: Score: X/10
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    score = _score_from_text(text)
    return score, text


def _refine(idea: dict, critique: str, niche: str, brief: dict, claude_client) -> dict:
    prompt = f"""You are refining a lead magnet idea for {niche} consultants based on critic feedback.

CURRENT IDEA:
Title: {idea["title"]}
Format: {idea["format"]}
Audience: {idea["audience"]}
Angle: {idea["angle"]}
Core Promise: {idea["core_promise"]}
Outline Seed: {idea["outline_seed"]}

CRITIC FEEDBACK:
{critique}

Revise the idea to address the critic's objections. Keep the format ({idea["format"]}).
Return a single JSON object with the same keys as before (title, format, audience, angle,
core_promise, outline_seed, impact, effort). No prose.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"```\w*\n?", "", raw).strip().rstrip("```").strip()
    return json.loads(raw)


def _score_from_text(text: str) -> int:
    """Extract integer score from text containing 'Score: X/10'. Default 5."""
    match = re.search(r"[Ss]core[:\s]+(\d+)\s*/\s*10", text)
    if match:
        return int(match.group(1))
    return 5


def _summarise_past(past_content: list[dict]) -> str:
    if not past_content:
        return "No past lead magnets on record."
    lines = []
    for item in past_content:
        m = item["meta"]
        i = item.get("impact", {})
        lines.append(
            f"- [{m.get('format', '?')}] {m.get('title', '?')} | "
            f"downloads: {i.get('downloads', '?')} | leads: {i.get('leads_generated', '?')}"
        )
    return "\n".join(lines)


def _make_plan_dict(idea: dict, niche: str) -> dict:
    slug = re.sub(r"[^a-z0-9]+", "-", idea["title"].lower()).strip("-")
    return {
        "slug": slug,
        "title": idea["title"],
        "format": idea["format"],
        "audience": idea.get("audience", ""),
        "angle": idea.get("angle", ""),
        "core_promise": idea.get("core_promise", ""),
        "outline_seed": idea.get("outline_seed", ""),
        "impact_score": idea.get("impact", 0),
        "effort_score": idea.get("effort", 0),
        "why_it_wins": idea.get("why_it_wins", ""),
        "critique_rounds": idea.get("critique_rounds", 0),
        "niche": niche,
    }


def _save_plan(plan: dict, critique_log: list[dict], state_dir: str) -> None:
    plans_dir = Path(state_dir) / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    slug = plan["slug"]
    (plans_dir / f"{slug}-plan.json").write_text(json.dumps(plan, indent=2))

    # Write critique log as markdown
    today = datetime.date.today().isoformat()
    lines = [f"# Critique Log: {plan['title']}\nDate: {today}\n"]
    for entry in critique_log:
        lines.append(f"## Round {entry['round']} — Score: {entry['score']}/10")
        lines.append(f"**Idea:** {entry['title']}\n")
        lines.append(entry["rationale"])
        lines.append("")
    (plans_dir / f"{slug}-critique-log.md").write_text("\n".join(lines))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_lead_magnet_planner.py -v
```

Expected: all 7 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add lead_magnet_agent/planner.py tests/test_lead_magnet_planner.py
git commit -m "feat(lead-magnet): add planner.py with brainstorm, scoring, and critique loop"
```

---

## Task 4: `writer.py` — doc renderer

**Files:**
- Create: `lead_magnet_agent/writer.py` (doc mode only for now)
- Create: `tests/test_lead_magnet_writer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_lead_magnet_writer.py
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from lead_magnet_agent.writer import write_artifact


PLAN_DOC = {
    "slug": "ai-marketing-playbook",
    "title": "AI Marketing Playbook",
    "format": "doc",
    "audience": "Senior marketing consultants",
    "angle": "Step-by-step guide to AI automation",
    "core_promise": "Automate 80% of reporting in 30 days",
    "outline_seed": "6-section white paper covering tools, workflows, and ROI",
    "niche": "marketing consultant",
}


def _make_claude_doc():
    mock = MagicMock()
    outline_json = '[{"title": "Introduction", "purpose": "Set the scene"}, {"title": "The Tools", "purpose": "Key AI tools"}]'
    critique_outline = "PASS: Flow is logical and delivers the promise."
    section_text = "<p>This is section content about marketing automation.</p>"
    critique_section = "PASS: Specific and credible."

    mock.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=outline_json)]),       # brainstorm_outline
        MagicMock(content=[MagicMock(text=critique_outline)]),   # critique_outline
        MagicMock(content=[MagicMock(text=section_text)]),       # write section 1
        MagicMock(content=[MagicMock(text=critique_section)]),   # critique section 1
        MagicMock(content=[MagicMock(text=section_text)]),       # write section 2
        MagicMock(content=[MagicMock(text=critique_section)]),   # critique section 2
    ]
    return mock


def test_write_artifact_doc_creates_html_file(tmp_path):
    write_artifact(
        plan=PLAN_DOC,
        output_dir=str(tmp_path),
        claude_client=_make_claude_doc(),
    )
    files = list(tmp_path.glob("*.html"))
    assert len(files) == 1


def test_write_artifact_doc_html_contains_title(tmp_path):
    write_artifact(
        plan=PLAN_DOC,
        output_dir=str(tmp_path),
        claude_client=_make_claude_doc(),
    )
    html = (tmp_path / "artifact.html").read_text()
    assert "AI Marketing Playbook" in html


def test_write_artifact_doc_saves_outline(tmp_path):
    write_artifact(
        plan=PLAN_DOC,
        output_dir=str(tmp_path),
        claude_client=_make_claude_doc(),
    )
    assert (tmp_path / "outline.md").exists()


def test_write_artifact_doc_saves_critique_log(tmp_path):
    write_artifact(
        plan=PLAN_DOC,
        output_dir=str(tmp_path),
        claude_client=_make_claude_doc(),
    )
    assert (tmp_path / "critique.md").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_lead_magnet_writer.py -v
```

Expected: `ImportError: cannot import name 'write_artifact'`

- [ ] **Step 3: Implement `writer.py` (doc mode)**

```python
# lead_magnet_agent/writer.py
"""Format-aware artifact generator: doc | dataset | app."""
from __future__ import annotations
import json
import re
from pathlib import Path


def write_artifact(
    plan: dict,
    output_dir: str,
    claude_client,
) -> str:
    """
    Generate the final artifact based on plan["format"].
    Returns path to the primary artifact file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    fmt = plan["format"]
    if fmt == "doc":
        return _write_doc(plan, out, claude_client)
    elif fmt == "dataset":
        return _write_dataset(plan, out, claude_client)
    elif fmt == "app":
        return _write_app(plan, out, claude_client)
    else:
        raise ValueError(f"Unknown format: {fmt}")


# ── DOC ──────────────────────────────────────────────────────────────────────

def _write_doc(plan: dict, out: Path, claude_client) -> str:
    outline = _brainstorm_outline(plan, claude_client)
    critique = _critique_outline(outline, plan, claude_client)
    _save_outline(outline, critique, out)

    sections = []
    critique_log = [f"# Writer Critique Log: {plan['title']}\n"]
    for section in outline:
        body = _write_section(section, plan, claude_client)
        sec_critique = _critique_section(section, body, plan, claude_client)
        critique_log.append(f"## {section['title']}\n{sec_critique}\n")
        sections.append((section["title"], body))

    html = _render_doc_html(plan, sections)
    artifact_path = out / "artifact.html"
    artifact_path.write_text(html)
    (out / "critique.md").write_text("\n".join(critique_log))
    return str(artifact_path)


def _brainstorm_outline(plan: dict, claude_client) -> list[dict]:
    prompt = f"""You are creating a white paper / guide for {plan["niche"]} consultants.

LEAD MAGNET:
Title: {plan["title"]}
Audience: {plan["audience"]}
Core Promise: {plan["core_promise"]}
Angle: {plan["angle"]}
Outline Seed: {plan["outline_seed"]}

Design 5-7 sections for this document. Each section should have a clear, specific purpose
that builds toward delivering the core promise.

Return a JSON array of objects, each with:
- title: string (section title)
- purpose: string (one sentence — what this section delivers)

Return JSON only. No prose.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"```\w*\n?", "", raw).strip().rstrip("```").strip()
    return json.loads(raw)


def _critique_outline(outline: list[dict], plan: dict, claude_client) -> str:
    sections_str = "\n".join(f"{i+1}. {s['title']} — {s['purpose']}" for i, s in enumerate(outline))
    prompt = f"""Review this outline for a lead magnet titled "{plan["title"]}".
Core Promise: {plan["core_promise"]}

OUTLINE:
{sections_str}

Does the flow lead logically to delivering the core promise?
Is any section generic filler that adds no value?
Start your response with PASS or FAIL, then explain in 2-3 sentences.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _write_section(section: dict, plan: dict, claude_client) -> str:
    prompt = f"""Write the "{section["title"]}" section for a lead magnet titled "{plan["title"]}".

TARGET AUDIENCE: {plan["audience"]}
CORE PROMISE: {plan["core_promise"]}
THIS SECTION'S PURPOSE: {section["purpose"]}

Write 200-400 words of substantive, specific content. No fluff.
Use real examples, frameworks, or data points where possible.
Return clean HTML fragments only (use <h2>, <p>, <ul>, <li> tags).
Do NOT include <html>, <head>, or <body> tags.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _critique_section(section: dict, body: str, plan: dict, claude_client) -> str:
    prompt = f"""Review this section of a lead magnet for {plan["niche"]} consultants.

SECTION: {section["title"]}
PURPOSE: {section["purpose"]}

CONTENT:
{body[:1000]}

Does this section deliver on its stated purpose?
Is it specific enough to be credible, or is it generic consulting fluff?
Start with PASS or FAIL. Then give ONE specific fix if needed (1-2 sentences max).
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _save_outline(outline: list[dict], critique: str, out: Path) -> None:
    lines = ["# Outline\n"]
    for i, s in enumerate(outline):
        lines.append(f"{i+1}. **{s['title']}** — {s['purpose']}")
    lines.append(f"\n## Outline Critique\n{critique}")
    (out / "outline.md").write_text("\n".join(lines))


def _render_doc_html(plan: dict, sections: list[tuple[str, str]]) -> str:
    sections_html = ""
    for title, body in sections:
        sections_html += f'<section class="section">\n{body}\n</section>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{plan["title"]}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; color: #1a1a1a; line-height: 1.7; }}
  h1 {{ font-size: 2.2rem; margin-bottom: 0.5rem; }}
  .subtitle {{ font-size: 1.1rem; color: #555; margin-bottom: 2rem; }}
  .section {{ margin-bottom: 2.5rem; border-top: 1px solid #eee; padding-top: 1.5rem; }}
  h2 {{ font-size: 1.5rem; color: #222; }}
  ul {{ padding-left: 1.5rem; }}
  li {{ margin-bottom: 0.4rem; }}
</style>
</head>
<body>
<h1>{plan["title"]}</h1>
<p class="subtitle">{plan["core_promise"]} — for {plan["audience"]}</p>
{sections_html}
</body>
</html>"""


# ── DATASET ──────────────────────────────────────────────────────────────────

def _write_dataset(plan: dict, out: Path, claude_client) -> str:
    dataset = _generate_dataset(plan, claude_client)
    critique = _critique_dataset(dataset, plan, claude_client)
    (out / "critique.md").write_text(f"# Dataset Critique\n\n{critique}")

    # Save raw CSV
    csv_path = out / "dataset.csv"
    csv_path.write_text(dataset["csv"])

    # Generate viz page
    viz_html = _generate_viz_page(plan, dataset, claude_client)
    artifact_path = out / "artifact.html"
    artifact_path.write_text(viz_html)
    return str(artifact_path)


def _generate_dataset(plan: dict, claude_client) -> dict:
    prompt = f"""You are creating a dataset lead magnet titled "{plan["title"]}".

AUDIENCE: {plan["audience"]}
CORE PROMISE: {plan["core_promise"]}
ANGLE: {plan["angle"]}
OUTLINE SEED: {plan["outline_seed"]}

Generate a realistic, research-backed dataset of 30-50 rows relevant to this lead magnet.
Base data on known industry benchmarks, publicly available statistics, and plausible estimates.
Label any estimated values clearly.

Return a JSON object with:
- headers: list of column name strings
- rows: list of lists (each inner list = one row, same order as headers)
- notes: string explaining data sources and any estimates

Return JSON only. No prose.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"```\w*\n?", "", raw).strip().rstrip("```").strip()
    data = json.loads(raw)

    # Build CSV string
    lines = [",".join(f'"{h}"' for h in data["headers"])]
    for row in data["rows"]:
        lines.append(",".join(f'"{str(v)}"' for v in row))
    data["csv"] = "\n".join(lines)
    return data


def _critique_dataset(dataset: dict, plan: dict, claude_client) -> str:
    sample_rows = dataset["rows"][:5]
    prompt = f"""Review this dataset for credibility and usefulness as a lead magnet.

TITLE: {plan["title"]}
COLUMNS: {", ".join(dataset["headers"])}
SAMPLE ROWS (first 5):
{json.dumps(sample_rows, indent=2)}

NOTES: {dataset.get("notes", "")}

Is the data specific and credible? Would a {plan["audience"]} find it genuinely useful?
Start with PASS or FAIL. Give ONE specific improvement if needed.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _generate_viz_page(plan: dict, dataset: dict, claude_client) -> str:
    headers_str = ", ".join(dataset["headers"])
    sample = json.dumps({"headers": dataset["headers"], "rows": dataset["rows"][:10]}, indent=2)
    prompt = f"""Create a self-contained HTML page that visualises this dataset as a lead magnet.

TITLE: {plan["title"]}
AUDIENCE: {plan["audience"]}
CORE PROMISE: {plan["core_promise"]}

DATASET SAMPLE (first 10 rows shown — full dataset embedded separately):
{sample}

Requirements:
- Self-contained single HTML file with inline CSS and JS
- Use Chart.js from CDN for at least one chart
- Include a summary table of the data
- Clean, professional design
- Include a download note: "Download the full CSV for all data"
- Embed the full CSV inline as a JS variable so users can copy it

Return the complete HTML file. No prose before or after.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ── APP ───────────────────────────────────────────────────────────────────────

def _write_app(plan: dict, out: Path, claude_client) -> str:
    app_html = _generate_app(plan, claude_client)
    critique = _critique_app(app_html, plan, claude_client)
    (out / "critique.md").write_text(f"# App Critique\n\n{critique}")

    if critique.startswith("FAIL"):
        app_html = _apply_app_fix(app_html, critique, plan, claude_client)

    artifact_path = out / "artifact.html"
    artifact_path.write_text(app_html)
    return str(artifact_path)


def _generate_app(plan: dict, claude_client) -> str:
    prompt = f"""Build a self-contained interactive HTML/JS mini-app as a lead magnet.

TITLE: {plan["title"]}
AUDIENCE: {plan["audience"]}
CORE PROMISE: {plan["core_promise"]}
ANGLE: {plan["angle"]}
DESCRIPTION: {plan["outline_seed"]}

Requirements:
- Single self-contained HTML file (all CSS and JS inline)
- Interactive: the user inputs data or answers questions and gets a result
- The result must deliver the core promise concretely (a score, a plan, a diagnosis, etc.)
- Clean, professional UI — use a modern sans-serif font and a clear colour scheme
- Mobile-friendly (responsive)
- No external dependencies except CDN links if needed (prefer vanilla JS)
- End with a clear CTA: "Get personalised recommendations — enter your email"
  (just the UI prompt — no backend required)

Return the complete HTML file. No prose before or after.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _critique_app(app_html: str, plan: dict, claude_client) -> str:
    prompt = f"""Review this interactive HTML/JS mini-app as a lead magnet for {plan["audience"]}.

TITLE: {plan["title"]}
CORE PROMISE: {plan["core_promise"]}

APP HTML (first 3000 chars):
{app_html[:3000]}

Does it deliver the core promise concretely?
Is the UX clear — would a user know what to do immediately?
Start with PASS or FAIL. Give ONE specific fix if the app fails.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _apply_app_fix(app_html: str, critique: str, plan: dict, claude_client) -> str:
    prompt = f"""Revise this HTML/JS mini-app based on the following critique.

CRITIQUE:
{critique}

CURRENT APP (first 4000 chars):
{app_html[:4000]}

Apply the fix described in the critique. Return the complete revised HTML file. No prose.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_lead_magnet_writer.py -v
```

Expected: all 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add lead_magnet_agent/writer.py tests/test_lead_magnet_writer.py
git commit -m "feat(lead-magnet): add writer.py with doc, dataset, and app renderers"
```

---

## Task 5: Add dataset and app writer tests

**Files:**
- Modify: `tests/test_lead_magnet_writer.py`

- [ ] **Step 1: Add dataset and app tests**

Append to `tests/test_lead_magnet_writer.py`:

```python
PLAN_DATASET = {
    "slug": "ai-marketing-benchmark-dataset",
    "title": "2026 AI Marketing Benchmark Dataset",
    "format": "dataset",
    "audience": "Marketing directors",
    "angle": "Industry benchmarks for AI adoption",
    "core_promise": "See where your team stands vs industry",
    "outline_seed": "50-row CSV with AI adoption rates by company size and vertical",
    "niche": "marketing consultant",
}

PLAN_APP = {
    "slug": "ai-marketing-audit-tool",
    "title": "AI Marketing Audit Tool",
    "format": "app",
    "audience": "Marketing VPs",
    "angle": "Self-assessment scoring AI readiness",
    "core_promise": "Know your AI readiness score in 5 minutes",
    "outline_seed": "10-question quiz with scored output and recommendations",
    "niche": "marketing consultant",
}


def _make_claude_dataset():
    mock = MagicMock()
    dataset_json = json.dumps({
        "headers": ["Company Size", "AI Adoption Rate", "Top Tool"],
        "rows": [["1-50", "12%", "ChatGPT"], ["51-200", "34%", "HubSpot AI"]],
        "notes": "Based on 2025 Gartner survey estimates."
    })
    critique_response = "PASS: Data is specific and credible."
    viz_html = "<html><body><h1>Dataset Viz</h1></body></html>"
    mock.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=dataset_json)]),
        MagicMock(content=[MagicMock(text=critique_response)]),
        MagicMock(content=[MagicMock(text=viz_html)]),
    ]
    return mock


def _make_claude_app():
    mock = MagicMock()
    app_html = "<html><body><h1>AI Audit Tool</h1><script>// quiz logic</script></body></html>"
    critique_response = "PASS: Delivers the core promise clearly."
    mock.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=app_html)]),
        MagicMock(content=[MagicMock(text=critique_response)]),
    ]
    return mock


def _make_claude_app_fail_then_pass():
    mock = MagicMock()
    app_html = "<html><body><h1>App</h1></body></html>"
    critique_fail = "FAIL: The UX is unclear. Add a visible start button above the fold."
    app_html_fixed = "<html><body><h1>App</h1><button>Start Audit</button></body></html>"
    mock.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=app_html)]),
        MagicMock(content=[MagicMock(text=critique_fail)]),
        MagicMock(content=[MagicMock(text=app_html_fixed)]),
    ]
    return mock


def test_write_artifact_dataset_creates_html_and_csv(tmp_path):
    write_artifact(
        plan=PLAN_DATASET,
        output_dir=str(tmp_path),
        claude_client=_make_claude_dataset(),
    )
    assert (tmp_path / "artifact.html").exists()
    assert (tmp_path / "dataset.csv").exists()


def test_write_artifact_dataset_csv_has_headers(tmp_path):
    write_artifact(
        plan=PLAN_DATASET,
        output_dir=str(tmp_path),
        claude_client=_make_claude_dataset(),
    )
    csv_text = (tmp_path / "dataset.csv").read_text()
    assert "Company Size" in csv_text


def test_write_artifact_app_creates_html_file(tmp_path):
    write_artifact(
        plan=PLAN_APP,
        output_dir=str(tmp_path),
        claude_client=_make_claude_app(),
    )
    assert (tmp_path / "artifact.html").exists()


def test_write_artifact_app_applies_fix_on_fail(tmp_path):
    write_artifact(
        plan=PLAN_APP,
        output_dir=str(tmp_path),
        claude_client=_make_claude_app_fail_then_pass(),
    )
    html = (tmp_path / "artifact.html").read_text()
    assert "Start Audit" in html


def test_write_artifact_unknown_format_raises(tmp_path):
    bad_plan = {**PLAN_DOC, "format": "video"}
    with pytest.raises(ValueError, match="Unknown format"):
        write_artifact(plan=bad_plan, output_dir=str(tmp_path), claude_client=MagicMock())
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
pytest tests/test_lead_magnet_writer.py -v
```

Expected: all 9 tests `PASSED`

- [ ] **Step 3: Commit**

```bash
git add tests/test_lead_magnet_writer.py
git commit -m "test(lead-magnet): add dataset and app writer tests"
```

---

## Task 6: `run.py` — CLI orchestrator (init + plan + generate)

**Files:**
- Create: `lead_magnet_agent/run.py`
- Create: `tests/test_lead_magnet_run.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_lead_magnet_run.py
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from lead_magnet_agent.run import run_init, run_plan, run_generate


def _make_clients():
    claude = MagicMock()
    web = MagicMock()
    web.fetch.return_value = "Marketing consultant landing page text."
    web.search.return_value = "AI marketing trends 2026"
    claude.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Expert marketing consultant.")]
    )
    return claude, web


def test_run_init_creates_state_structure(tmp_path):
    claude, web = _make_clients()
    run_init(
        url="https://example.com",
        niche="marketing consultant",
        state_dir=str(tmp_path / "state"),
        claude_client=claude,
        web_client=web,
    )
    state = tmp_path / "state"
    assert (state / "profile.md").exists()
    assert (state / "niche.txt").exists()
    assert (state / "url.txt").read_text().strip() == "https://example.com"
    assert (state / "content").is_dir()
    assert (state / "plans").is_dir()
    assert (state / "output").is_dir()


def test_run_init_rejects_existing_state_without_force(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    claude, web = _make_clients()
    with pytest.raises(SystemExit):
        run_init(
            url="https://example.com",
            niche="marketing consultant",
            state_dir=str(state_dir),
            claude_client=claude,
            web_client=web,
        )


def test_run_init_force_overwrites(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    claude, web = _make_clients()
    # Should not raise
    run_init(
        url="https://example.com",
        niche="marketing consultant",
        state_dir=str(state_dir),
        claude_client=claude,
        web_client=web,
        force=True,
    )
    assert (state_dir / "profile.md").exists()


def _make_plan_json(state_dir: str, slug: str = "ai-audit-tool"):
    plans_dir = Path(state_dir) / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan = {
        "slug": slug, "title": "AI Audit Tool", "format": "app",
        "audience": "Marketing VPs", "angle": "Self-assessment",
        "core_promise": "Know your score", "outline_seed": "10-question quiz",
        "impact_score": 8, "effort_score": 3, "why_it_wins": "High value",
        "critique_rounds": 1, "niche": "marketing consultant",
    }
    (plans_dir / f"{slug}-plan.json").write_text(json.dumps(plan))
    return plan


def test_run_generate_creates_output_dir(tmp_path):
    state_dir = str(tmp_path / "state")
    Path(state_dir).mkdir()
    plan = _make_plan_json(state_dir)

    claude = MagicMock()
    app_html = "<html><body><h1>Audit Tool</h1></body></html>"
    critique = "PASS: Delivers the promise."
    claude.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=app_html)]),
        MagicMock(content=[MagicMock(text=critique)]),
    ]

    run_generate(
        slug=plan["slug"],
        state_dir=state_dir,
        claude_client=claude,
    )

    output_dir = Path(state_dir) / "output" / plan["slug"]
    assert (output_dir / "artifact.html").exists()
    assert (output_dir / "plan.json").exists()


def test_run_generate_errors_if_plan_not_found(tmp_path):
    state_dir = str(tmp_path / "state")
    Path(state_dir).mkdir()
    (Path(state_dir) / "plans").mkdir()
    claude = MagicMock()
    with pytest.raises(SystemExit):
        run_generate(slug="nonexistent", state_dir=state_dir, claude_client=claude)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_lead_magnet_run.py -v
```

Expected: `ImportError: cannot import name 'run_init'`

- [ ] **Step 3: Implement `run.py`**

```python
# lead_magnet_agent/run.py
"""CLI orchestrator: init | plan | generate."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from lead_magnet_agent.web import WebClient
from lead_magnet_agent.researcher import build_research_brief
from lead_magnet_agent.planner import build_plan
from lead_magnet_agent.writer import write_artifact


def _make_clients():
    load_dotenv()
    import anthropic
    claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    web = WebClient(openclaw_api_key=os.environ.get("OPENCLAW_API_KEY", ""))
    return claude, web


def run_init(
    url: str,
    niche: str,
    state_dir: str,
    claude_client,
    web_client,
    force: bool = False,
) -> None:
    state = Path(state_dir)
    if state.exists() and not force:
        print(f"ERROR: {state_dir} already exists. Pass --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    # Create directory structure
    for subdir in ("content", "plans", "output"):
        (state / subdir).mkdir(parents=True, exist_ok=True)

    # Fetch and extract profile
    print("[1/3] Fetching landing page and extracting profile...")
    page_text = web_client.fetch(url) or ""
    profile = _extract_profile(page_text, niche, claude_client)

    # Save state files
    (state / "profile.md").write_text(profile)
    (state / "niche.txt").write_text(niche)
    (state / "url.txt").write_text(url)

    print(f"[2/3] State directory created at {state_dir}")
    print("[3/3] Done.\n")
    print(f"Profile saved to {state_dir}/profile.md")
    print(f"Add past lead magnets to {state_dir}/content/<slug>/")
    print(f"  Each slug needs meta.json and impact.json (see docs for format)")
    print(f"\nNext: run `lead-magnet-agent plan --state-dir {state_dir}`")


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


def run_plan(
    state_dir: str,
    claude_client,
    web_client,
    topic_hint: str | None = None,
) -> None:
    state = Path(state_dir)
    niche = (state / "niche.txt").read_text().strip()
    url = (state / "url.txt").read_text().strip()

    print("[1/3] Running research phase...")
    brief = build_research_brief(
        url=url,
        niche=niche,
        state_dir=state_dir,
        claude_client=claude_client,
        web_client=web_client,
    )

    print("[2/3] Running planning phase (brainstorm → critique loop)...")
    plan = build_plan(
        brief=brief,
        state_dir=state_dir,
        claude_client=claude_client,
        topic_hint=topic_hint,
    )

    print("[3/3] Done.\n")
    _print_concept_card(plan)
    print(f"\nPlan saved to {state_dir}/plans/{plan['slug']}-plan.json")
    print(f"\nApprove this concept? Run:")
    print(f"  lead-magnet-agent generate {plan['slug']} --state-dir {state_dir}")


def _print_concept_card(plan: dict) -> None:
    print("=" * 60)
    print("LEAD MAGNET CONCEPT")
    print("=" * 60)
    print(f"Format:       {plan['format']}")
    print(f"Title:        {plan['title']}")
    print(f"Audience:     {plan['audience']}")
    print(f"Angle:        {plan['angle']}")
    print(f"Core Promise: {plan['core_promise']}")
    print(f"Why it wins:  {plan['why_it_wins'][:200]}")
    print(f"Impact score: {plan['impact_score']}/10  |  Effort score: {plan['effort_score']}/10")
    print(f"Critique rounds: {plan['critique_rounds']}")
    print("=" * 60)


def run_generate(
    slug: str,
    state_dir: str,
    claude_client,
) -> None:
    state = Path(state_dir)
    plan_path = state / "plans" / f"{slug}-plan.json"

    if not plan_path.exists():
        print(f"ERROR: No plan found at {plan_path}. Run `plan` first.", file=sys.stderr)
        sys.exit(1)

    plan = json.loads(plan_path.read_text())
    output_dir = state / "output" / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save a copy of the plan alongside the output
    (output_dir / "plan.json").write_text(json.dumps(plan, indent=2))

    print(f"[generate] Writing {plan['format']} artifact: {plan['title']}...")
    artifact_path = write_artifact(
        plan=plan,
        output_dir=str(output_dir),
        claude_client=claude_client,
    )

    print(f"\nDone. Artifact written to: {artifact_path}")
    if (output_dir / "outline.md").exists():
        print(f"Outline: {output_dir}/outline.md")
    print(f"Critique log: {output_dir}/critique.md")


def main():
    parser = argparse.ArgumentParser(prog="lead-magnet-agent")
    sub = parser.add_subparsers(dest="mode", required=True)

    init_p = sub.add_parser("init", help="Initialise state directory from a landing page URL")
    init_p.add_argument("url")
    init_p.add_argument("--niche", required=True)
    init_p.add_argument("--state-dir", default="state")
    init_p.add_argument("--force", action="store_true")

    plan_p = sub.add_parser("plan", help="Research + brainstorm + critique → surface best concept")
    plan_p.add_argument("--state-dir", default="state")
    plan_p.add_argument("--topic-hint", default=None)

    gen_p = sub.add_parser("generate", help="Generate the artifact from an approved plan")
    gen_p.add_argument("slug")
    gen_p.add_argument("--state-dir", default="state")

    args = parser.parse_args()
    claude, web = _make_clients()

    if args.mode == "init":
        run_init(args.url, args.niche, args.state_dir, claude, web, force=args.force)
    elif args.mode == "plan":
        run_plan(args.state_dir, claude, web, topic_hint=args.topic_hint)
    elif args.mode == "generate":
        run_generate(args.slug, args.state_dir, claude)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_lead_magnet_run.py -v
```

Expected: all 5 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add lead_magnet_agent/run.py tests/test_lead_magnet_run.py
git commit -m "feat(lead-magnet): add run.py CLI orchestrator with init, plan, generate modes"
```

---

## Task 7: Full test suite pass + integration smoke test

**Files:**
- No new files

- [ ] **Step 1: Run the full test suite**

```bash
cd /home/bilelburaway/dev/Aagency
pytest tests/test_lead_magnet_researcher.py tests/test_lead_magnet_planner.py tests/test_lead_magnet_writer.py tests/test_lead_magnet_run.py -v
```

Expected: all tests `PASSED`, zero failures

- [ ] **Step 2: Verify CLI is importable as a module**

```bash
cd /home/bilelburaway/dev/Aagency
python -c "from lead_magnet_agent.run import main; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Verify entry point resolves (dry run)**

```bash
python -m lead_magnet_agent.run --help
```

Expected: usage text showing `init`, `plan`, `generate` subcommands

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(lead-magnet): complete lead magnet agent — all tests passing"
```

---

## Improvement Areas (from spec)

1. **Dynamic critique threshold** — current hard cap is 5 rounds; a future version exits early at ≥7 (already implemented) but could also allow continuation beyond 5 if score is still < 4, with a stop at 10.
2. **Multi-idea surfacing** — currently surfaces one winner; a future `--top-n 3` flag could present the top 3 with trade-offs.
3. **Automated impact tracking** — `impact.json` is populated manually; a webhook/counter integration would close the feedback loop.
4. **Dataset sourcing** — currently synthesises data from web search; real public API sources would improve credibility.
5. **App testing** — generated HTML/JS apps are not programmatically tested; a Playwright validation step could catch broken JS before delivery.
