# linkedin_agent/scraper.py
"""LinkedIn scraping via Playwright (headed Chrome + existing session) + raw-posts.txt fallback."""
from __future__ import annotations
import re
import time
import random
import shutil
import tempfile
from pathlib import Path

# Candidate Chrome executables in order of preference (Linux / macOS)
_CHROME_CANDIDATES = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/opt/google/chrome/google-chrome",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

# Default Chrome user-data directories per platform
_CHROME_USER_DATA_DEFAULTS = [
    Path.home() / ".config" / "google-chrome",          # Linux
    Path.home() / "Library" / "Application Support" / "Google" / "Chrome",  # macOS
]


def _find_chrome_executable() -> str | None:
    """Return the path to the Chrome binary, or None if not found."""
    for path in _CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    return shutil.which("google-chrome") or shutil.which("google-chrome-stable")


def _find_chrome_user_data() -> str | None:
    """Return Chrome's default user-data directory, or None if not found."""
    for path in _CHROME_USER_DATA_DEFAULTS:
        if path.exists():
            return str(path)
    return None


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
    Scrape ~50 most recent posts from a LinkedIn profile using Playwright + Chrome.

    Uses Chrome's existing user-data directory so the current login session is
    reused — no bot-detection friction from a fresh browser context.
    Falls back to a Playwright storage-state file (auth_path) if Chrome's profile
    directory cannot be located, then prompts for manual login as a last resort.

    Returns list of {text, date, likes, comments} dicts.
    Raises RuntimeError with fallback instructions on failure.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "playwright not installed. Run: pip install playwright && playwright install chrome"
        )

    chrome_exe = _find_chrome_executable()
    if not chrome_exe:
        raise RuntimeError(
            "Google Chrome not found. Install Chrome or set CHROME_EXECUTABLE env var."
        )

    chrome_user_data = _find_chrome_user_data()
    auth_file = Path(auth_path)
    auth_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        if chrome_user_data:
            # Copy Chrome profile to a temp dir so Playwright doesn't conflict
            # with a running Chrome instance (locked profile directory).
            print(f"[scraper] Copying Chrome profile from: {chrome_user_data}")
            print("[scraper] This may take a few seconds...")
            tmp_dir = tempfile.mkdtemp(prefix="chrome_playwright_")
            try:
                # Only copy the Default profile to keep it fast and small
                src_default = Path(chrome_user_data) / "Default"
                dst_default = Path(tmp_dir) / "Default"
                shutil.copytree(
                    str(src_default), str(dst_default),
                    ignore=shutil.ignore_patterns("Singleton*"),
                    dirs_exist_ok=False,
                )
            except Exception as e:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                raise RuntimeError(f"Failed to copy Chrome profile: {e}")

            print("[scraper] Launching browser with copied profile...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=tmp_dir,
                executable_path=chrome_exe,
                headless=False,
                timeout=30_000,
                args=[
                    "--profile-directory=Default",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-session-crashed-bubble",
                    "--disable-infobars",
                    "--restore-last-session=false",
                ],
            )
            page = context.new_page()
        else:
            # Fallback: fresh Chrome window with optional saved storage state
            print("[scraper] Chrome profile not found; falling back to storage-state auth.")
            launch_kwargs: dict = {"executable_path": chrome_exe, "headless": False}
            browser = p.chromium.launch(**launch_kwargs)
            context_kwargs: dict = {}
            if auth_file.exists():
                context_kwargs["storage_state"] = str(auth_file)
            context = browser.new_context(**context_kwargs)
            page = context.new_page()

        # Navigate to profile
        page.goto(linkedin_url, wait_until="load", timeout=60_000)
        _human_delay()

        # If not logged in, pause for user
        if "login" in page.url or "authwall" in page.url:
            print("\n[scraper] Please log in to LinkedIn in the browser window.")
            print("[scraper] Press Enter here once you are logged in...")
            input()
            _human_delay()

        # Persist session to storage-state file (useful for the fallback path)
        if not chrome_user_data:
            context.storage_state(path=str(auth_file))

        try:
            posts = _extract_posts(page, linkedin_url)
        finally:
            context.close()
            if chrome_user_data and 'tmp_dir' in locals():
                shutil.rmtree(tmp_dir, ignore_errors=True)
        return posts


def _human_delay():
    time.sleep(random.uniform(0.5, 1.5))


def _extract_posts(page, profile_url: str) -> list[dict]:
    """Scroll and extract posts from LinkedIn profile page."""
    posts = []
    seen_texts = set()

    # Navigate to posts tab
    posts_url = profile_url.rstrip("/") + "/recent-activity/shares/"
    page.goto(posts_url, wait_until="load", timeout=60_000)
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
