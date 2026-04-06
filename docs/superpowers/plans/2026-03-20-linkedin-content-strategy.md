# LinkedIn Content Strategy Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI pipeline that scrapes LinkedIn posts, derives a content strategy, generates 8-week post batches with images, and iterates every cycle based on engagement ratings.

**Architecture:** Seven modules under `linkedin_agent/` with a shared `state/` directory for persistence. `run.py` is the CLI orchestrator for three modes (`init`, `generate`, `review`). All external web calls go through `web.py`, all Claude calls are made directly via the `anthropic` SDK in each module.

**Tech Stack:** Python 3.11, `anthropic`, `playwright`, `httpx`, `beautifulsoup4`, `openclaw` (CMDOP wrapper — used for web search via `agent.run()`), `duckduckgo-search` (fallback), `pytest`, `python-dotenv`

---

## Verified Tech Notes (from pre-plan research)

- **openclaw** (`pip install openclaw`) wraps the CMDOP SDK. Its `CMDOPClient.agent.run(prompt, output_model=Model)` runs a remote AI agent that has web search tools when configured. Requires `OPENCLAW_API_KEY` in env.
- **CMDOP** does NOT have a native `search()` or `fetch()` method — web.py wraps `agent.run()` for search, and uses `httpx` directly for URL fetch.
- **httpx** and **beautifulsoup4** are already installed (pulled in by `anthropic`/`cmdop`).
- **Image search** uses CMDOP agent with a structured Pydantic output model; falls back to `None` on failure.

---

## File Map

```
linkedin_agent/
├── web.py           # httpx fetch + CMDOP agent.run() for search/image
├── scraper.py       # Playwright LinkedIn auth + post scraping
├── analyzer.py      # Claude: voice + theme analysis
├── strategist.py    # Claude: build/update strategy.md
├── generator.py     # Claude: slot plan + 24-post generation
├── reviewer.py      # CLI rating loop + review.md writer
└── run.py           # CLI: init | generate | review

tests/
├── test_web.py
├── test_analyzer.py
├── test_strategist.py
├── test_generator.py
├── test_reviewer.py
└── test_run.py

state/              # created at runtime — committed except .auth/
  .auth/            # gitignored
  current-cycle.txt
  niche.txt         # niche string from --niche arg (reused by generate/review)
  linkedin-url.txt  # LinkedIn profile URL (reused by review for re-scraping)
  raw-posts.txt     # manual fallback
  strategy.md
  cycle-01/
    slot-plan.json
    week-01-post-1.md
    ...
    review.md

requirements.txt
.env.example
pytest.ini
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `linkedin_agent/__init__.py` (empty)
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `pytest.ini`
- Modify: `.gitignore` (add state/.auth/ entry)

- [ ] **Step 1: Create the directory and empty init**

```bash
mkdir -p linkedin_agent tests
touch linkedin_agent/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```
anthropic
playwright
openclaw
duckduckgo-search
python-dotenv
beautifulsoup4
pytest
pytest-mock
```

- [ ] **Step 3: Write .env.example**

```
ANTHROPIC_API_KEY=sk-ant-...
OPENCLAW_API_KEY=cmdop_live_...
```

- [ ] **Step 4: Write pytest.ini**

```ini
[pytest]
testpaths = tests
```

- [ ] **Step 5: Append to .gitignore**

```
state/.auth/
.env
__pycache__/
*.pyc
```

- [ ] **Step 6: Commit**

```bash
git add linkedin_agent/ tests/ requirements.txt .env.example pytest.ini .gitignore
git commit -m "feat: scaffold linkedin_agent module structure"
```

---

## Task 2: web.py — URL Fetch

**Files:**
- Create: `linkedin_agent/web.py`
- Create: `tests/test_web.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_web.py
from unittest.mock import MagicMock, patch
from linkedin_agent.web import WebClient

def test_fetch_returns_text(tmp_path):
    client = WebClient(openclaw_api_key="fake")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    with patch("linkedin_agent.web.httpx.get", return_value=mock_response):
        result = client.fetch("https://example.com")
    assert "Hello world" in result

def test_fetch_returns_none_after_retries(tmp_path):
    client = WebClient(openclaw_api_key="fake")
    with patch("linkedin_agent.web.httpx.get", side_effect=Exception("timeout")):
        result = client.fetch("https://example.com")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_web.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'linkedin_agent.web'`

- [ ] **Step 3: Implement web.py fetch**

```python
# linkedin_agent/web.py
from __future__ import annotations
import time
import httpx
from bs4 import BeautifulSoup


class WebClient:
    def __init__(self, openclaw_api_key: str):
        self._api_key = openclaw_api_key
        self._cmdop = None  # lazy init on first search/image_search call

    def _get_cmdop(self):
        if self._cmdop is None:
            from openclaw import OpenClaw
            self._cmdop = OpenClaw.remote(api_key=self._api_key)
        return self._cmdop

    def fetch(self, url: str) -> str | None:
        """Fetch a URL and return readable text. Returns None on final failure."""
        for attempt in range(3):
            try:
                resp = httpx.get(url, timeout=15, follow_redirects=True,
                                 headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_web.py::test_fetch_returns_text tests/test_web.py::test_fetch_returns_none_after_retries -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/web.py tests/test_web.py
git commit -m "feat: add web.py fetch with retry"
```

---

## Task 3: web.py — Search and Image Search

**Files:**
- Modify: `linkedin_agent/web.py`
- Modify: `tests/test_web.py`

- [ ] **Step 1: Write failing tests for search and image_search**

```python
# append to tests/test_web.py
from unittest.mock import MagicMock, patch

def test_search_returns_text(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_result = MagicMock()
    mock_result.text = "AI trends 2026: agents everywhere."
    mock_cmdop.agent.run.return_value = mock_result
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.search("AI LinkedIn trends")
    assert result is not None
    assert "AI" in result

def test_search_returns_none_on_failure(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_cmdop.agent.run.side_effect = Exception("API error")
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.search("AI LinkedIn trends")
    assert result is None

def test_image_search_returns_dict(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_result = MagicMock()
    mock_result.data = MagicMock(
        url="https://unsplash.com/photo.jpg",
        source_domain="unsplash.com",
        photographer="Jane Doe"
    )
    mock_cmdop.agent.run.return_value = mock_result
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.image_search("AI robot office")
    assert result["url"] == "https://unsplash.com/photo.jpg"
    assert result["photographer"] == "Jane Doe"

def test_image_search_returns_none_on_failure(mocker):
    client = WebClient(openclaw_api_key="fake")
    mock_cmdop = MagicMock()
    mock_cmdop.agent.run.side_effect = Exception("timeout")
    mocker.patch.object(client, "_get_cmdop", return_value=mock_cmdop)
    result = client.image_search("AI robot office")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_web.py -k "search or image" -v
```
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Implement search and image_search in web.py**

Append to `WebClient` class in `linkedin_agent/web.py`:

```python
    def search(self, query: str) -> str | None:
        """Web search via CMDOP agent. Returns top-result summary text. None on failure."""
        prompt = (
            f"Search the web for: {query}\n"
            f"Return a concise summary (max 200 words) of the most relevant findings. "
            f"Focus on recent, factual content."
        )
        for attempt in range(3):
            try:
                client = self._get_cmdop()
                result = client.agent.run(prompt)
                return result.text
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None

    def image_search(self, query: str) -> dict | None:
        """Find a relevant image via CMDOP agent. Returns {url, source_domain, photographer} or None."""
        from pydantic import BaseModel

        class ImageResult(BaseModel):
            url: str
            source_domain: str
            photographer: str | None = None

        prompt = (
            f"Find a high-quality, freely usable image for: {query}\n"
            f"Prefer images from Unsplash, Pexels, or Pixabay. "
            f"Return the direct image URL, the source domain, and photographer name if available."
        )
        for attempt in range(3):
            try:
                client = self._get_cmdop()
                result = client.agent.run(prompt, output_model=ImageResult)
                if result.data:
                    return {
                        "url": result.data.url,
                        "source_domain": result.data.source_domain,
                        "photographer": result.data.photographer,
                    }
                return None
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None
```

- [ ] **Step 4: Run all web tests**

```bash
pytest tests/test_web.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/web.py tests/test_web.py
git commit -m "feat: add web.py search and image_search via CMDOP agent"
```

---

## Task 4: scraper.py

**Files:**
- Create: `linkedin_agent/scraper.py`
- Create: `tests/test_scraper.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_scraper.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scraper.py -v
```
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement scraper.py**

```python
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
        raise RuntimeError("playwright not installed. Run: pip install playwright && playwright install chromium")

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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_scraper.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/scraper.py tests/test_scraper.py
git commit -m "feat: add scraper.py with Playwright scraping and raw-posts fallback"
```

---

## Task 5: analyzer.py

**Files:**
- Create: `linkedin_agent/analyzer.py`
- Create: `tests/test_analyzer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_analyzer.py
import json
import pytest
from unittest.mock import MagicMock, patch
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_analyzer.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement analyzer.py**

```python
# linkedin_agent/analyzer.py
"""Analyzes scraped LinkedIn posts to extract voice, themes, and benchmarks."""
from __future__ import annotations
import json


def analyze_posts(
    posts: list[dict],
    niche: str,
    claude_client,
    web_client,
) -> dict:
    """
    Analyze posts and return a dict with voice, themes, cadence, gaps,
    top_performers, trend_context, benchmark_context.
    """
    trend_context = web_client.search(f"{niche} LinkedIn trends") or ""
    benchmark_context = web_client.search(f"top LinkedIn influencers {niche}") or ""

    posts_text = "\n\n---\n\n".join(
        f"Date: {p.get('date','')}\nLikes: {p.get('likes',0)}\nComments: {p.get('comments',0)}\n\n{p['text']}"
        for p in posts
    )

    system = (
        "You are a LinkedIn content strategist. "
        "Analyze the provided posts and return JSON only — no prose."
    )
    user = f"""Analyze these LinkedIn posts for a {niche} professional.

POSTS:
{posts_text}

INDUSTRY TRENDS:
{trend_context}

TOP INFLUENCER BENCHMARKS:
{benchmark_context}

Return a JSON object with these exact keys:
- voice: string describing writing style and tone
- themes: list of strings (recurring content topics, most frequent first)
- cadence: string describing posting frequency
- gaps: list of strings (content types they haven't tried but should)
- top_performers: list of strings (first 100 chars of 3 highest-engagement posts)
- trend_context: string (2-3 sentence summary of industry trends)
- benchmark_context: string (2-3 sentence summary of influencer benchmarks)
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_analyzer.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/analyzer.py tests/test_analyzer.py
git commit -m "feat: add analyzer.py for voice and theme extraction"
```

---

## Task 6: strategist.py

**Files:**
- Create: `linkedin_agent/strategist.py`
- Create: `tests/test_strategist.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_strategist.py
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
    (state_dir / "strategy.md").write_text("# Old Strategy\n")

    mock_claude = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="# Content Strategy — Cycle 2\nUpdated.")]
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_strategist.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement strategist.py**

```python
# linkedin_agent/strategist.py
"""Builds and updates content strategy from analysis and review data."""
from __future__ import annotations
import datetime
from pathlib import Path


_STRATEGY_TEMPLATE = """# Content Strategy — Cycle {cycle}
Generated: {today} | Next review: {next_review}

## Voice & Tone
{voice}

## Core Themes (ranked by past performance)
{themes}

## Content Mix (per 8-week cycle)
- 40% thought leadership (contrarian takes)
- 30% behind-the-scenes / build-in-public
- 20% tactical how-tos
- 10% personal story

## Posting Cadence
3× per week — Mon / Wed / Fri

## What's Working
{whats_working}

## What to Avoid
{what_to_avoid}

## Industry Context
{industry_context}
"""


def build_strategy(
    landing_text: str,
    analysis: dict,
    niche: str,
    state_dir: str,
    cycle: int,
    claude_client,
) -> None:
    """Generate strategy.md from landing page + analysis. Overwrites any existing file."""
    today = datetime.date.today().isoformat()
    next_review = (datetime.date.today() + datetime.timedelta(days=56)).isoformat()

    themes_str = "\n".join(
        f"{i+1}. {t}" for i, t in enumerate(analysis.get("themes", []))
    )

    user = f"""You are a LinkedIn content strategist for a {niche} professional.

LANDING PAGE:
{landing_text[:2000]}

VOICE ANALYSIS: {analysis.get('voice', '')}
THEMES: {', '.join(analysis.get('themes', []))}
CONTENT GAPS: {', '.join(analysis.get('gaps', []))}
INDUSTRY TRENDS: {analysis.get('trend_context', '')}
BENCHMARKS: {analysis.get('benchmark_context', '')}

Write the "What's Working", "What to Avoid", and "Industry Context" sections for a cycle 1 strategy.
- What's Working: empty for cycle 1 (no engagement data yet). Write: "[No data yet — cycle 1]"
- What to Avoid: based on gaps analysis. 2-3 bullets.
- Industry Context: 3-4 sentences summarizing trends and benchmarks. Max 120 words.

Return only these three sections as plain text, separated by "|||".
Format: <whats_working>|||<what_to_avoid>|||<industry_context>
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": user}],
    )
    parts = response.content[0].text.strip().split("|||")
    whats_working = parts[0].strip() if len(parts) > 0 else "[No data yet — cycle 1]"
    what_to_avoid = parts[1].strip() if len(parts) > 1 else ""
    industry_context = parts[2].strip() if len(parts) > 2 else analysis.get("trend_context", "")

    strategy = _STRATEGY_TEMPLATE.format(
        cycle=cycle,
        today=today,
        next_review=next_review,
        voice=analysis.get("voice", ""),
        themes=themes_str,
        whats_working=whats_working,
        what_to_avoid=what_to_avoid,
        industry_context=industry_context,
    )
    Path(state_dir, "strategy.md").write_text(strategy)


def update_strategy(
    review_md: str,
    niche: str,
    state_dir: str,
    cycle: int,
    claude_client,
) -> None:
    """
    Archive current strategy.md to strategy-cycle-{N}.md,
    then generate a new strategy.md using review data.
    """
    state = Path(state_dir)
    current = state / "strategy.md"
    old_text = current.read_text() if current.exists() else ""

    # Archive old strategy
    archive_name = f"strategy-cycle-{cycle:02d}.md"
    (state / archive_name).write_text(old_text)

    today = datetime.date.today().isoformat()
    next_review = (datetime.date.today() + datetime.timedelta(days=56)).isoformat()

    user = f"""You are a LinkedIn content strategist for a {niche} professional.

CURRENT STRATEGY:
{old_text[:2000]}

REVIEW DATA (engagement + ratings from last 8 weeks):
{review_md[:1500]}

Update the strategy for cycle {cycle + 1}. Write these three sections only, separated by "|||":
1. What's Working: bullet points of what drove high ratings/engagement
2. What to Avoid: bullet points of what to drop or reduce
3. Industry Context: 3-4 sentences of updated trends for the next cycle

Format: <whats_working>|||<what_to_avoid>|||<industry_context>
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": user}],
    )
    try:
        parts = response.content[0].text.strip().split("|||")
        if len(parts) < 3:
            raise ValueError(f"Expected 3 sections separated by '|||', got {len(parts)}")
        whats_working = parts[0].strip()
        what_to_avoid = parts[1].strip()
        industry_context = parts[2].strip()
    except (ValueError, IndexError) as e:
        print(f"WARNING: Could not parse strategy update sections: {e}. Using placeholders.")
        whats_working = "[Review review.md manually — parsing failed]"
        what_to_avoid = "[Review review.md manually — parsing failed]"
        industry_context = "[Update manually]"

    # Build new strategy — preserve themes/voice from old, update working/avoid/context
    import re
    voice_match = re.search(r"## Voice & Tone\n(.+?)(?=\n##)", old_text, re.DOTALL)
    if voice_match:
        voice = voice_match.group(1).strip()
    else:
        print("WARNING: Could not parse Voice & Tone from old strategy. Using placeholder.")
        voice = "[Review strategy.md — Voice & Tone section not found]"
    themes_match = re.search(r"## Core Themes.*?\n(.+?)(?=\n##)", old_text, re.DOTALL)
    if themes_match:
        themes = themes_match.group(1).strip()
    else:
        print("WARNING: Could not parse Core Themes from old strategy. Using placeholder.")
        themes = "[Review strategy.md — Core Themes section not found]"

    strategy = _STRATEGY_TEMPLATE.format(
        cycle=cycle + 1,
        today=today,
        next_review=next_review,
        voice=voice,
        themes=themes,
        whats_working=whats_working,
        what_to_avoid=what_to_avoid,
        industry_context=industry_context,
    )
    current.write_text(strategy)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_strategist.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/strategist.py tests/test_strategist.py
git commit -m "feat: add strategist.py for strategy generation and update"
```

---

## Task 7: generator.py

**Files:**
- Create: `linkedin_agent/generator.py`
- Create: `tests/test_generator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_generator.py
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, call
from linkedin_agent.generator import build_slot_plan, generate_posts

SAMPLE_STRATEGY = """# Content Strategy — Cycle 1
Generated: 2026-03-20

## Content Mix (per 8-week cycle)
- 40% thought leadership (contrarian takes)
- 30% behind-the-scenes / build-in-public
- 20% tactical how-tos
- 10% personal story
"""

def test_build_slot_plan_returns_24_slots(mocker):
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
    assert slots[2]["week"] == 1  # 3 posts per week
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_generator.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement generator.py**

```python
# linkedin_agent/generator.py
"""Generates 8-week post batches (slot plan + per-post Claude calls)."""
from __future__ import annotations
import json
import re
from pathlib import Path


_CONTENT_MIX = {
    "contrarian": 10,       # ~40% of 24
    "behind-the-scenes": 7, # ~30%
    "how-to": 5,            # ~20%
    "story": 2,             # ~10%
}


def build_slot_plan(
    strategy_md: str,
    niche: str,
    claude_client,
    web_client,
) -> list[dict]:
    """
    Returns list of 24 slot dicts:
    {week, position, hook_type, topic}
    Weeks 1-8, positions 1-3 per week (3 posts/week × 8 weeks = 24).
    """
    trend_context = web_client.search(f"{niche} news this week") or ""

    # Build week/position skeleton
    skeleton = []
    hook_types = []
    for hook, count in _CONTENT_MIX.items():
        hook_types.extend([hook] * count)
    # Distribute evenly: alternate hook types across weeks
    for i, hook in enumerate(hook_types):
        week = (i // 3) + 1
        position = (i % 3) + 1
        skeleton.append({"week": week, "position": position, "hook_type": hook})

    user = f"""You are a LinkedIn content strategist for {niche}.

CONTENT STRATEGY:
{strategy_md[:1500]}

CURRENT TRENDS:
{trend_context}

Assign a specific, engaging topic to each of these 24 post slots.
Vary topics across weeks. Make topics timely and relevant to {niche}.

Return a JSON array of 24 objects, each with "hook_type" and "topic" keys only.
Do not include week or position — just the 24 objects in order.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"```\w*\n?", "", raw).strip().rstrip("```").strip()
    topics = json.loads(raw)

    slots = []
    for i, (skel, topic_data) in enumerate(zip(skeleton, topics)):
        slots.append({
            "week": skel["week"],
            "position": skel["position"],
            "hook_type": topic_data.get("hook_type", skel["hook_type"]),
            "topic": topic_data.get("topic", f"Topic {i+1}"),
        })
    return slots


def generate_posts(
    cycle_dir: str,
    slots: list[dict],
    strategy_md: str,
    voice_posts: list[dict],
    claude_client,
    web_client,
) -> None:
    """
    Generate one markdown file per slot in cycle_dir.
    Skips slots where the file already exists (resume on interrupt).
    """
    out = Path(cycle_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Pick 5 shortest voice examples
    sorted_posts = sorted(voice_posts, key=lambda p: len(p.get("text", "")))
    examples = sorted_posts[:5]
    voice_section = "\n\n---\n\n".join(p["text"] for p in examples)

    for slot in slots:
        week = slot["week"]
        pos = slot["position"]
        filename = f"week-{week:02d}-post-{pos}.md"
        dest = out / filename
        if dest.exists():
            continue  # resume: skip already-generated posts

        news = web_client.search(f"{slot['topic']} news this week") or ""
        image_data = web_client.image_search(slot.get("image_query", slot["topic"]))

        user = f"""Write a LinkedIn post for a {slot['hook_type']} style post.

TOPIC: {slot['topic']}
WEEK: {week} of 8, POST: {pos} of 3

CONTENT STRATEGY (follow this voice and mix):
{strategy_md[:800]}

VOICE EXAMPLES (match this author's style):
{voice_section[:600]}

CURRENT NEWS HOOK:
{news[:200]}

Instructions:
- Write the post body only (no frontmatter, no title)
- 150-300 words
- Strong opening hook
- Conversational, not corporate
- End with a question or CTA
- On the last line, write: image_query: <3-5 word image search query>
"""
        response = claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": user}],
        )
        full_text = response.content[0].text.strip()

        # Extract image_query from last line
        image_query = slot["topic"]
        lines = full_text.splitlines()
        if lines and lines[-1].startswith("image_query:"):
            image_query = lines[-1].split(":", 1)[1].strip()
            post_body = "\n".join(lines[:-1]).strip()
        else:
            post_body = full_text

        if image_data is None:
            image_url = "null  # MANUAL"
            image_credit = "null  # MANUAL"
        else:
            image_url = image_data["url"]
            credit_parts = []
            if image_data.get("photographer"):
                credit_parts.append(f"Photo by {image_data['photographer']}")
            if image_data.get("source_domain"):
                credit_parts.append(f"on {image_data['source_domain']}")
            image_credit = " ".join(credit_parts) if credit_parts else "null"

        md = f"""---
week: {week}
post: {pos}
topic: {slot['topic']}
hook_type: {slot['hook_type']}
status: draft
published_text_snippet: ""
published_url: ""
image_url: {image_url}
image_credit: "{image_credit}"
image_query: "{image_query}"
---

{post_body}
"""
        dest.write_text(md)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_generator.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/generator.py tests/test_generator.py
git commit -m "feat: add generator.py with slot plan and 24-post generation"
```

---

## Task 8: reviewer.py

**Files:**
- Create: `linkedin_agent/reviewer.py`
- Create: `tests/test_reviewer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_reviewer.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_reviewer.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement reviewer.py**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_reviewer.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/reviewer.py tests/test_reviewer.py
git commit -m "feat: add reviewer.py CLI rating loop"
```

---

## Task 9: run.py — init mode

**Files:**
- Create: `linkedin_agent/run.py`
- Create: `tests/test_run.py`

- [ ] **Step 1: Write failing test for init**

```python
# tests/test_run.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

def test_init_creates_state_structure(tmp_path, monkeypatch):
    """init mode creates state/, writes current-cycle.txt=1, writes niche.txt, generates slot-plan.json."""
    monkeypatch.chdir(tmp_path)

    mock_anthropic = MagicMock()
    # Claude calls: analyzer, strategist (build_strategy prompt), slot plan, 2 post generations
    def _make_msg(text):
        m = MagicMock()
        m.content = [MagicMock(text=text)]
        return m

    import json as _json
    analysis_result = _json.dumps({
        "voice": "Direct", "themes": ["AI"], "cadence": "2x/week",
        "gaps": [], "top_performers": [], "trend_context": "", "benchmark_context": ""
    })
    slot_plan = _json.dumps([
        {"hook_type": "contrarian", "topic": f"Topic {i}"} for i in range(24)
    ])
    mock_anthropic.messages.create.side_effect = [
        _make_msg(analysis_result),    # analyzer call
        _make_msg("Working|||Avoid|||Context"),  # strategist call
        _make_msg(slot_plan),          # slot plan call
    ] + [_make_msg("Post body.\nimage_query: AI")] * 24  # 24 post generations

    mock_web = MagicMock()
    mock_web.fetch.return_value = "I help build AI products."
    mock_web.search.return_value = "AI trends."
    mock_web.image_search.return_value = None

    mock_scraper_posts = [{"text": "Sample post.", "date": "2026-01-01", "likes": 10, "comments": 1}]

    with patch("linkedin_agent.run._make_clients", return_value=(mock_anthropic, mock_web)), \
         patch("linkedin_agent.run.scrape_posts", return_value=mock_scraper_posts):
        from linkedin_agent.run import run_init
        run_init(
            landing_page_url="https://example.com",
            linkedin_url="https://linkedin.com/in/test",
            niche="AI product management",
            state_dir=str(tmp_path / "state"),
        )

    state = tmp_path / "state"
    assert (state / "current-cycle.txt").read_text().strip() == "1"
    assert (state / "niche.txt").read_text().strip() == "AI product management"
    assert (state / "strategy.md").exists()
    assert (state / "cycle-01" / "slot-plan.json").exists()
    assert len(list((state / "cycle-01").glob("week-*-post-*.md"))) == 24
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_run.py::test_init_creates_state_structure -v
```
Expected: FAIL

- [ ] **Step 3: Implement run.py init mode**

```python
# linkedin_agent/run.py
"""CLI orchestrator: init | generate | review"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from linkedin_agent.web import WebClient
from linkedin_agent.scraper import scrape_posts, parse_raw_posts
from linkedin_agent.analyzer import analyze_posts
from linkedin_agent.strategist import build_strategy, update_strategy
from linkedin_agent.generator import build_slot_plan, generate_posts
from linkedin_agent.reviewer import collect_ratings


def _make_clients():
    """Load env and return (anthropic_client, web_client)."""
    load_dotenv()
    import anthropic
    claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    web = WebClient(openclaw_api_key=os.environ.get("OPENCLAW_API_KEY", ""))
    return claude, web


def _read_state(state_dir: str, filename: str) -> str:
    return (Path(state_dir) / filename).read_text().strip()


def _write_state(state_dir: str, filename: str, content: str) -> None:
    path = Path(state_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def run_init(
    landing_page_url: str,
    linkedin_url: str,
    niche: str,
    state_dir: str,
    force: bool = False,
) -> None:
    state = Path(state_dir)
    if state.exists() and not force:
        print(f"ERROR: {state_dir} already exists. Pass --force to overwrite.", file=sys.stderr)
        sys.exit(1)
    state.mkdir(parents=True, exist_ok=True)
    (state / ".auth").mkdir(exist_ok=True)

    claude, web = _make_clients()

    print("[1/6] Fetching landing page...")
    landing_text = web.fetch(landing_page_url) or ""

    print("[2/6] Scraping LinkedIn posts...")
    auth_path = str(state / ".auth" / "linkedin.json")
    raw_posts_path = str(state / "raw-posts.txt")
    try:
        posts = scrape_posts(linkedin_url, auth_path)
    except RuntimeError as e:
        print(f"\nWARNING: {e}")
        print(f"\nManually populate {raw_posts_path} in this format:")
        print("---\ndate: 2026-01-15\nlikes: 42\ncomments: 7\ntext:\nYour post text here.\n---")
        input("\nPress Enter once you have populated raw-posts.txt...")
        posts = parse_raw_posts(raw_posts_path)
        if not posts:
            print("ERROR: No posts found in raw-posts.txt. Exiting.", file=sys.stderr)
            sys.exit(1)

    print("[3/6] Analyzing posts...")
    analysis = analyze_posts(posts, niche, claude, web)

    print("[4/6] Building strategy...")
    build_strategy(landing_text, analysis, niche, state_dir, cycle=1, claude_client=claude)

    print("[5/6] Setting up cycle 1...")
    _write_state(state_dir, "current-cycle.txt", "1")
    _write_state(state_dir, "niche.txt", niche)
    _write_state(state_dir, "linkedin-url.txt", linkedin_url)
    cycle_dir = state / "cycle-01"
    cycle_dir.mkdir(exist_ok=True)

    print("[6/6] Generating slot plan and 24 posts...")
    strategy_md = (state / "strategy.md").read_text()
    slots = build_slot_plan(strategy_md, niche, claude, web)
    (cycle_dir / "slot-plan.json").write_text(json.dumps(slots, indent=2))

    # Use shortest 5 posts for voice calibration
    voice_posts = sorted(posts, key=lambda p: len(p.get("text", "")))[:5]
    generate_posts(str(cycle_dir), slots, strategy_md, voice_posts, claude, web)

    print(f"\nDone. 24 posts written to {cycle_dir}/")
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_run.py::test_init_creates_state_structure -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/run.py tests/test_run.py
git commit -m "feat: add run.py init mode"
```

---

## Task 10: run.py — generate and review modes + CLI

**Files:**
- Modify: `linkedin_agent/run.py`
- Modify: `tests/test_run.py`

- [ ] **Step 1: Write failing tests for generate and review**

```python
# append to tests/test_run.py

def test_generate_advances_cycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    (state / "current-cycle.txt").write_text("1")
    (state / "niche.txt").write_text("AI product management")
    (state / "strategy.md").write_text("# Strategy\n## Content Mix\n- 40% contrarian\n- 30% behind-the-scenes\n- 20% how-to\n- 10% story\n")

    import json as _json
    def _make_msg(text):
        m = MagicMock()
        m.content = [MagicMock(text=text)]
        return m
    slot_plan = _json.dumps([{"hook_type": "contrarian", "topic": f"T{i}"} for i in range(24)])

    mock_anthropic = MagicMock()
    mock_anthropic.messages.create.side_effect = [
        _make_msg(slot_plan),
    ] + [_make_msg("Post body.\nimage_query: AI")] * 24

    mock_web = MagicMock()
    mock_web.search.return_value = "trends"
    mock_web.image_search.return_value = None

    with patch("linkedin_agent.run._make_clients", return_value=(mock_anthropic, mock_web)):
        from linkedin_agent.run import run_generate
        run_generate(state_dir=str(state))

    assert (state / "current-cycle.txt").read_text().strip() == "2"
    assert (state / "cycle-02").exists()
    assert len(list((state / "cycle-02").glob("week-*-post-*.md"))) == 24

def test_review_archives_strategy_and_calls_generate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    (state / "current-cycle.txt").write_text("1")
    (state / "niche.txt").write_text("AI product management")
    (state / "strategy.md").write_text("# Old Strategy\n## Voice & Tone\nDirect\n## Core Themes\n1. AI\n## Content Mix\n- 40% contrarian\n- 30% behind-the-scenes\n- 20% how-to\n- 10% story\n")
    cycle_dir = state / "cycle-01"
    cycle_dir.mkdir()
    # Make 2 post files
    for i in range(1, 3):
        (cycle_dir / f"week-01-post-{i}.md").write_text(f"---\nweek: 1\npost: {i}\ntopic: AI\nhook_type: contrarian\nstatus: draft\npublished_text_snippet: \"\"\npublished_url: \"\"\nimage_url: null\nimage_credit: null\nimage_query: \"AI\"\n---\n\nPost body.")

    import json as _json
    def _make_msg(text):
        m = MagicMock()
        m.content = [MagicMock(text=text)]
        return m
    slot_plan = _json.dumps([{"hook_type": "contrarian", "topic": f"T{i}"} for i in range(24)])

    mock_anthropic = MagicMock()
    mock_anthropic.messages.create.side_effect = [
        _make_msg("Working|||Avoid|||Context"),  # update_strategy
        _make_msg(slot_plan),                    # slot plan
    ] + [_make_msg("Post body.\nimage_query: AI")] * 24

    mock_web = MagicMock()
    mock_web.search.return_value = "trends"
    mock_web.image_search.return_value = None

    # Simulate user inputs: rate both posts
    monkeypatch.setattr("builtins.input", lambda _: "3")

    with patch("linkedin_agent.run._make_clients", return_value=(mock_anthropic, mock_web)), \
         patch("linkedin_agent.run.scrape_posts", return_value=[]):
        from linkedin_agent.run import run_review
        run_review(state_dir=str(state))

    assert (state / "strategy-cycle-01.md").exists()
    assert (state / "current-cycle.txt").read_text().strip() == "2"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_run.py -k "generate or review" -v
```
Expected: FAIL

- [ ] **Step 3: Implement generate, review, and CLI in run.py**

Append to `linkedin_agent/run.py`:

```python
def run_generate(state_dir: str) -> None:
    state = Path(state_dir)
    n = int(_read_state(state_dir, "current-cycle.txt"))
    niche = _read_state(state_dir, "niche.txt")
    strategy_md = (state / "strategy.md").read_text()

    next_n = n + 1
    next_cycle_label = f"cycle-{next_n:02d}"
    next_cycle_dir = state / next_cycle_label

    # Check for review context from current cycle
    review_path = state / f"cycle-{n:02d}" / "review.md"
    review_context = review_path.read_text() if review_path.exists() else ""

    print(f"[generate] Advancing to cycle {next_n}...")
    _write_state(state_dir, "current-cycle.txt", str(next_n))
    next_cycle_dir.mkdir(exist_ok=True)

    claude, web = _make_clients()

    # Optional: incorporate review into generation context (pass as part of strategy)
    effective_strategy = strategy_md
    if review_context:
        effective_strategy += f"\n\n## Previous Cycle Review\n{review_context}"

    # Reuse existing slot plan if interrupted mid-generation
    slot_plan_path = next_cycle_dir / "slot-plan.json"
    if slot_plan_path.exists():
        print(f"[generate] Reusing existing slot plan from {slot_plan_path}")
        slots = json.loads(slot_plan_path.read_text())
    else:
        slots = build_slot_plan(effective_strategy, niche, claude, web)
        slot_plan_path.write_text(json.dumps(slots, indent=2))

    # No voice posts available for generate mode (would need to re-scrape)
    generate_posts(str(next_cycle_dir), slots, strategy_md, [], claude, web)
    print(f"Done. 24 posts written to {next_cycle_dir}/")


def run_review(state_dir: str) -> None:
    state = Path(state_dir)
    n = int(_read_state(state_dir, "current-cycle.txt"))
    niche = _read_state(state_dir, "niche.txt")
    cycle_label = f"cycle-{n:02d}"
    cycle_dir = state / cycle_label
    auth_path = str(state / ".auth" / "linkedin.json")

    print(f"[review] Reviewing cycle {n}...")

    # Re-scrape engagement data
    linkedin_url_path = state / "linkedin-url.txt"
    scraped_posts = []
    if linkedin_url_path.exists():
        linkedin_url = linkedin_url_path.read_text().strip()
        try:
            scraped_posts = scrape_posts(linkedin_url, auth_path)
        except RuntimeError as e:
            print(f"WARNING: Scrape failed — {e}")
            print("Proceeding with ratings-only review (no engagement data).")

    collect_ratings(str(cycle_dir), scraped_posts)

    review_md = (cycle_dir / "review.md").read_text()
    strategy_md = (state / "strategy.md").read_text()

    claude, _ = _make_clients()
    print("[review] Updating strategy...")
    update_strategy(review_md, niche, state_dir, cycle=n, claude_client=claude)

    print("[review] Generating next cycle...")
    run_generate(state_dir)


def main():
    parser = argparse.ArgumentParser(prog="linkedin-agent")
    sub = parser.add_subparsers(dest="mode", required=True)

    init_p = sub.add_parser("init")
    init_p.add_argument("landing_page_url")
    init_p.add_argument("linkedin_url")
    init_p.add_argument("--niche", required=True)
    init_p.add_argument("--force", action="store_true")
    init_p.add_argument("--state-dir", default="state")

    gen_p = sub.add_parser("generate")
    gen_p.add_argument("--state-dir", default="state")

    rev_p = sub.add_parser("review")
    rev_p.add_argument("--state-dir", default="state")

    args = parser.parse_args()
    if args.mode == "init":
        run_init(args.landing_page_url, args.linkedin_url, args.niche,
                 args.state_dir, force=args.force)
    elif args.mode == "generate":
        run_generate(args.state_dir)
    elif args.mode == "review":
        run_review(args.state_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add linkedin_agent/run.py tests/test_run.py
git commit -m "feat: add run.py generate/review modes and CLI entry point"
```

---

## Task 11: Integration Test + Final Wiring

**Files:**
- Create: `tests/test_integration.py`
- Modify: `linkedin_agent/run.py` (save linkedin_url in init)

- [ ] **Step 1: Write smoke integration test**

```python
# tests/test_integration.py
"""Smoke test: verifies the full init → generate → review cycle without real APIs."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


def _make_claude_side_effects():
    """Build a side_effect list for all Claude calls in the full cycle."""
    def msg(text):
        m = MagicMock()
        m.content = [MagicMock(text=text)]
        return m

    analysis = json.dumps({
        "voice": "Direct", "themes": ["AI"], "cadence": "2x/week",
        "gaps": [], "top_performers": [], "trend_context": "", "benchmark_context": ""
    })
    slot_24 = json.dumps([{"hook_type": "contrarian", "topic": f"T{i}"} for i in range(24)])
    return (
        [msg(analysis)]                          # init: analyze
        + [msg("W|||A|||C")]                     # init: build_strategy
        + [msg(slot_24)]                         # init: slot plan
        + [msg("Body.\nimage_query: AI")] * 24   # init: 24 posts
        + [msg("W2|||A2|||C2")]                  # review: update_strategy
        + [msg(slot_24)]                         # review→generate: slot plan
        + [msg("Body.\nimage_query: AI")] * 24   # review→generate: 24 posts
    )


def test_full_cycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: "3")  # rate all posts 3

    mock_claude = MagicMock()
    mock_claude.messages.create.side_effect = _make_claude_side_effects()

    mock_web = MagicMock()
    mock_web.fetch.return_value = "I build AI products."
    mock_web.search.return_value = "AI trends."
    mock_web.image_search.return_value = None

    sample_posts = [{"text": "AI is great.", "date": "2026-01-01", "likes": 10, "comments": 1}]

    state = str(tmp_path / "state")

    with patch("linkedin_agent.run._make_clients", return_value=(mock_claude, mock_web)), \
         patch("linkedin_agent.run.scrape_posts", return_value=sample_posts):
        from linkedin_agent.run import run_init, run_review
        run_init("https://ex.com", "https://linkedin.com/in/test", "AI PM", state)
        run_review(state_dir=state)

    s = Path(state)
    assert (s / "current-cycle.txt").read_text().strip() == "2"
    assert (s / "strategy-cycle-01.md").exists()
    assert len(list((s / "cycle-02").glob("week-*-post-*.md"))) == 24
```

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ -v
```
Expected: all PASS

- [ ] **Step 4: Final commit**

```bash
git add linkedin_agent/run.py tests/test_integration.py
git commit -m "feat: complete linkedin_agent pipeline with integration test"
```

---

## Setup Note

Before running for real (not tests), install Playwright browsers:

```bash
pip install -r requirements.txt
playwright install chromium
```

First run:
```bash
python -m linkedin_agent.run init https://yoursite.com https://linkedin.com/in/you --niche "your niche"
```
