import textwrap
import pytest
from linkedin_agent.scraper import parse_raw_posts


def test_parse_raw_posts_basic(tmp_path):
    raw = tmp_path / "raw-posts.txt"
    raw.write_text(textwrap.dedent("""\
        ---
        date: 2026-01-15
        likes: 42
        comments: 7
        text:
        This is post one.
        It spans two lines.
        ---
        date: 2026-01-10
        likes: 18
        comments: 2
        text:
        Another post.
        ---
    """))
    posts = parse_raw_posts(str(raw))
    assert len(posts) == 2
    assert posts[0]["likes"] == 42
    assert "post one" in posts[0]["text"]
    assert posts[1]["comments"] == 2


def test_parse_raw_posts_missing_file():
    posts = parse_raw_posts("/nonexistent/path.txt")
    assert posts == []


def test_parse_raw_posts_empty_blocks(tmp_path):
    raw = tmp_path / "raw-posts.txt"
    raw.write_text("---\n---\n")
    posts = parse_raw_posts(str(raw))
    assert posts == []
