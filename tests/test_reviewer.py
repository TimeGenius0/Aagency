import pytest
from pathlib import Path
from linkedin_agent.reviewer import collect_ratings, _match_posts


def _make_post_file(path: Path, week: int, pos: int, snippet: str = ""):
    path.write_text(f"""---
week: {week}
post: {pos}
topic: AI agents
hook_type: contrarian
status: draft
published_text_snippet: "{snippet}"
published_url: ""
image_url: null
image_credit: null
image_query: "AI"
---

This is the post body.
""")


def test_collect_ratings_writes_review(tmp_path, monkeypatch):
    cycle_dir = tmp_path / "cycle-01"
    cycle_dir.mkdir()
    _make_post_file(cycle_dir / "week-01-post-1.md", 1, 1, "AI agents are")
    _make_post_file(cycle_dir / "week-01-post-2.md", 1, 2)

    inputs = iter(["4", "s"])  # rate first 4, skip second
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    collect_ratings(
        cycle_dir=str(cycle_dir),
        scraped_posts=[{"text": "AI agents are everywhere.", "likes": 50, "comments": 3}],
    )
    review = (cycle_dir / "review.md").read_text()
    assert "rating: 4" in review
    assert "skipped: true" in review


def test_collect_ratings_resumes(tmp_path, monkeypatch):
    """Already-rated posts in review.md should be skipped."""
    cycle_dir = tmp_path / "cycle-01"
    cycle_dir.mkdir()
    _make_post_file(cycle_dir / "week-01-post-1.md", 1, 1)
    _make_post_file(cycle_dir / "week-01-post-2.md", 1, 2)

    # Pre-existing review for post 1
    (cycle_dir / "review.md").write_text("## week-01-post-1\nrating: 5\n\n")

    inputs = iter(["3"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    collect_ratings(cycle_dir=str(cycle_dir), scraped_posts=[])
    review = (cycle_dir / "review.md").read_text()
    # Post 1 still rated 5, not re-rated
    assert review.count("rating:") == 2
    assert "rating: 5" in review


def test_match_posts():
    scraped = [
        {"text": "AI agents are everywhere in 2026.", "likes": 10, "comments": 1},
        {"text": "How I shipped a product in 24 hours.", "likes": 5, "comments": 0},
    ]
    snippet = "AI agents are everywhere"
    result = _match_posts(snippet, scraped)
    assert result["likes"] == 10
