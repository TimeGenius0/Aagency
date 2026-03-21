# linkedin_agent/reviewer.py
"""CLI rating loop — collects user ratings per post and writes review.md incrementally."""
from __future__ import annotations
import re
from pathlib import Path


def collect_ratings(cycle_dir: str, scraped_posts: list[dict]) -> None:
    """
    For each post .md file in cycle_dir (sorted by week/post):
    - Skip if already rated in review.md
    - Match to scraped engagement data
    - Prompt user to rate 1-5 or 's' to skip
    - Append result to review.md immediately
    """
    cycle = Path(cycle_dir)
    review_path = cycle / "review.md"

    already_rated = _load_rated_slugs(review_path)

    post_files = sorted(cycle.glob("week-*-post-*.md"))
    for post_file in post_files:
        slug = post_file.stem
        if slug in already_rated:
            continue

        meta, body = _parse_post_file(post_file)
        snippet = meta.get("published_text_snippet", "").strip('"')
        scraped = _match_posts(snippet, scraped_posts) if snippet else None

        topic = meta.get("topic", "unknown topic")
        hook = meta.get("hook_type", "")
        print(f"\n{'='*60}")
        print(f"Post: {slug}  [{hook}]")
        print(f"Topic: {topic}")
        if scraped:
            print(f"Engagement: {scraped.get('likes', '?')} likes, {scraped.get('comments', '?')} comments")
        else:
            print("Engagement: unavailable")
        print(f"\nPreview: {body[:200]}...")

        while True:
            raw = input("\nRate this post 1–5 (or 's' to skip): ").strip().lower()
            if raw == "s":
                _append_review(review_path, slug, topic, scraped, rating=None, skipped=True)
                break
            if raw in {"1", "2", "3", "4", "5"}:
                _append_review(review_path, slug, topic, scraped, rating=int(raw), skipped=False)
                break
            print("Invalid input. Enter 1-5 or 's'.")


def _load_rated_slugs(review_path: Path) -> set[str]:
    if not review_path.exists():
        return set()
    text = review_path.read_text()
    return set(re.findall(r"^## (week-\d+-post-\d+)", text, re.MULTILINE))


def _parse_post_file(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if "---" not in text:
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta_text = parts[1]
    body = parts[2].strip()
    meta = {}
    for line in meta_text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


def _append_review(
    review_path: Path,
    slug: str,
    topic: str,
    scraped: dict | None,
    rating: int | None,
    skipped: bool,
) -> None:
    likes = scraped.get("likes", "unavailable") if scraped else "unavailable"
    comments = scraped.get("comments", "unavailable") if scraped else "unavailable"
    entry = f"## {slug}\n"
    entry += f"topic: {topic}\n"
    entry += f"likes: {likes}\n"
    entry += f"comments: {comments}\n"
    if skipped:
        entry += "skipped: true\n"
    else:
        entry += f"rating: {rating}\n"
    entry += "\n"
    with open(review_path, "a") as f:
        f.write(entry)


def _match_posts(snippet: str, scraped: list[dict]) -> dict | None:
    """Find the scraped post whose text starts with snippet (first 80 chars)."""
    if not snippet:
        return None
    needle = snippet[:80].lower()
    for post in scraped:
        if post.get("text", "").lower().startswith(needle):
            return post
    return None
