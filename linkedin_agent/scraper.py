# linkedin_agent/scraper.py
"""LinkedIn scraping via Playwright (headed, human-speed) + raw-posts.txt fallback."""
from __future__ import annotations
import re
import time
import random
from pathlib import Path


def parse_raw_posts(path: str) -> list[dict]:
    """Parse state/raw-posts.txt into list of post dicts. Returns [] on any error."""
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        return []

    posts = []
    blocks = re.split(r"(?m)^---\s*$", text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        post = {}
        lines = block.splitlines()
        text_lines = []
        in_text = False
        for line in lines:
            if in_text:
                text_lines.append(line)
            elif line.startswith("date:"):
                post["date"] = line.split(":", 1)[1].strip()
            elif line.startswith("likes:"):
                try:
                    post["likes"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    post["likes"] = 0
            elif line.startswith("comments:"):
                try:
                    post["comments"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    post["comments"] = 0
            elif line.strip() == "text:":
                in_text = True
        if text_lines:
            post["text"] = "\n".join(text_lines).strip()
        if post.get("text"):
            posts.append(post)
    return posts


def scrape_posts(linkedin_url: str, auth_path: str) -> list[dict]:
    """
    Scrape ~50 most recent posts from a LinkedIn profile using Playwright.
    Opens a headed browser. If auth_path session exists, reuses it.
    If not, pauses for user to log in and saves the session.
    Returns list of {text, date, likes, comments} dicts.
    Raises RuntimeError with fallback instructions on failure.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    auth_file = Path(auth_path)
    auth_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context_kwargs = {}
        if auth_file.exists():
            context_kwargs["storage_state"] = str(auth_file)

        browser = p.chromium.launch(headless=False)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        # Navigate to profile
        page.goto(linkedin_url, wait_until="networkidle")
        _human_delay()

        # If not logged in, pause for user
        if "login" in page.url or "authwall" in page.url:
            print("\n[scraper] Please log in to LinkedIn in the browser window.")
            print("[scraper] Press Enter here once you are logged in...")
            input()
            _human_delay()

        # Save session
        context.storage_state(path=str(auth_file))

        posts = _extract_posts(page, linkedin_url)
        browser.close()
        return posts


def _human_delay():
    time.sleep(random.uniform(0.5, 1.5))


def _extract_posts(page, profile_url: str) -> list[dict]:
    """Scroll and extract posts from LinkedIn profile page."""
    posts = []
    seen_texts = set()

    # Navigate to posts tab
    posts_url = profile_url.rstrip("/") + "/recent-activity/shares/"
    page.goto(posts_url, wait_until="networkidle")
    _human_delay()

    for _ in range(10):  # scroll up to 10 times
        page.evaluate("window.scrollBy(0, window.innerHeight)")
        _human_delay()

        cards = page.query_selector_all("[data-urn*='activity']")
        for card in cards:
            try:
                text_el = card.query_selector(".feed-shared-update-v2__description")
                if not text_el:
                    continue
                text = text_el.inner_text().strip()
                if not text or text in seen_texts:
                    continue
                seen_texts.add(text)

                date_el = card.query_selector("time")
                date_str = date_el.get_attribute("datetime") if date_el else ""

                likes_el = card.query_selector("[aria-label*='reaction']")
                likes = _parse_count(likes_el.inner_text() if likes_el else "0")

                comments_el = card.query_selector("[aria-label*='comment']")
                comments = _parse_count(comments_el.inner_text() if comments_el else "0")

                posts.append({
                    "text": text,
                    "date": date_str,
                    "likes": likes,
                    "comments": comments,
                })
                if len(posts) >= 50:
                    return posts
            except Exception:
                continue

    if len(posts) < 10:
        raise RuntimeError(
            f"LinkedIn scraping returned too few posts ({len(posts)}). "
            "LinkedIn may have changed their DOM or blocked the scrape. "
            "Populate state/raw-posts.txt manually (see spec for format) and re-run."
        )
    return posts


def _parse_count(text: str) -> int:
    text = text.strip().replace(",", "")
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else 0
