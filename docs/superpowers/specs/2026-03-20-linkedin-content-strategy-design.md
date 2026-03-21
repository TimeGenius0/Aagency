# LinkedIn Content Strategy Agent — Design Spec
Date: 2026-03-20 | Status: Approved

## Overview

A Python pipeline that scrapes a user's LinkedIn post history, analyzes their voice and performance, derives a content strategy from their landing page and industry trends, generates a full 8-week batch of draft posts (with images), and re-evaluates the strategy every 8 weeks based on engagement data and user ratings.

---

## Architecture

### Module Layout

```
linkedin_agent/
├── run.py           # Orchestrator: init | generate | review
├── scraper.py       # Playwright: LinkedIn auth + post scraping + engagement re-scrape
├── analyzer.py      # Claude + web.py: voice analysis, theme extraction, benchmarking
├── strategist.py    # Claude + web.py: build and update strategy.md from analysis output
├── generator.py     # Claude + web.py: generate 8-week post batch with news hooks + images
├── reviewer.py      # Playwright + Claude: collect engagement data + user ratings + re-strategize
└── web.py           # Openclaw wrapper: search, page fetch, image search
```

### State Layout

```
state/
├── .auth/              # Playwright saved auth session (gitignored)
├── current-cycle.txt   # Single source of truth for active cycle number (e.g. "1")
├── raw-posts.txt       # Manual fallback if scraper fails (see format below)
├── strategy.md         # Current content strategy (overwritten each cycle)
├── strategy-cycle-01.md  # Archived strategy from cycle 1 (never overwritten)
├── strategy-cycle-02.md  # Archived strategy from cycle 2
├── cycle-01/
│   ├── week-01-post-1.md
│   ├── week-01-post-2.md
│   ├── week-01-post-3.md
│   └── ...               # 24 posts total (3/week × 8 weeks)
│   └── review.md         # Engagement data + user ratings (written by `review` mode)
└── cycle-02/
    └── ...
```

**Gitignore:** `state/.auth/` is gitignored. Everything else in `state/` is committed — post drafts and strategies are the user's working document.

---

## Three Modes

### `init` — First Run

```
python run.py init <landing_page_url> <linkedin_url> --niche "<niche string>"
```

Example: `python run.py init https://bilel.ai https://linkedin.com/in/bilel --niche "AI product management"`

Exits with error if `state/` already exists, unless `--force` is passed.

Steps:
1. `run.py` calls `web.py.fetch(landing_page_url)` → returns page text → passed to `strategist.py`
2. `scraper.py` opens a visible Playwright browser (headed, human-speed delays) → pauses for user login → saves session to `state/.auth/linkedin.json` → scrapes last ~50 posts (text, date, approximate likes/comments)
3. `analyzer.py` sends posts to Claude → extracts voice, recurring themes, cadence, content gaps; calls `web.py.search(niche + " LinkedIn trends")` and `web.py.search("top LinkedIn influencers " + niche)` for trend and benchmark context
4. `strategist.py` receives landing page text + analyzer output → sends to Claude → writes `state/strategy.md`
5. `run.py` writes `state/current-cycle.txt` = `"1"` and creates `state/cycle-01/`
6. `generator.py` generates 24 posts one at a time (see generation prompt spec below) → writes to `state/cycle-01/week-XX-post-Y.md`

### `generate` — Next Cycle (without review)

```
python run.py generate
```

1. Reads `state/current-cycle.txt` → let this value be `N` (the completed cycle)
2. Reads `state/strategy.md`
3. Checks `state/cycle-{N}/review.md` — if it exists, passes it to `generator.py` as additional context; if it does not exist (user skipped review), proceeds with `strategy.md` only
4. Creates `state/cycle-{N+1}/`, writes `N+1` to `current-cycle.txt`
5. `generator.py` generates 24 posts → writes to `state/cycle-{N+1}/`

### `review` — 8-Week Re-evaluation

```
python run.py review
```

1. Reads `state/current-cycle.txt` → let this value be `N` (the cycle being reviewed)
2. `scraper.py` attempts to re-scrape the user's LinkedIn profile with headed Playwright (human-speed delays) → returns list of `{text_snippet, date, likes, comments}`. **If scraping fails:** prints a warning, skips engagement data for all posts, and proceeds to step 4 with engagement stats listed as "unavailable" — ratings-only review is still valid.
3. `reviewer.py` matches scraped posts to local `.md` files by comparing `published_text_snippet` frontmatter (first 80 chars). Unmatched local posts show `likes: ?, comments: ?`.
4. `reviewer.py` CLI loop: for each post in cycle `N`, prints topic + engagement stats (or "unavailable"), prompts `Rate this post 1–5 (or s to skip): `. Ratings written to `state/cycle-{N}/review.md` incrementally — session is resumable on restart (already-rated posts skipped).
5. Claude receives `strategy.md` + `review.md` → synthesizes what worked / what to avoid → produces updated strategy text
6. Old `state/strategy.md` is archived to `state/strategy-cycle-{N}.md` before overwriting
7. New strategy written to `state/strategy.md`; `Next review` date = today + 56 days
8. Automatically calls `generate` to produce the next cycle

---

## Data Formats

### Post Markdown Frontmatter

```yaml
---
week: 1
post: 2
topic: AI agents in product management
hook_type: contrarian         # contrarian | how-to | story | behind-the-scenes | news-hook
status: draft                 # draft | published | skipped
published_text_snippet: ""    # first 80 chars of actual published text (filled in by user after posting)
published_url: ""             # LinkedIn post URL (filled in by user after posting, optional)
image_url: https://...
image_credit: "Photo by Jane Doe on Unsplash"   # null if unavailable
image_query: "AI robot product manager office"
---
```

**Status lifecycle:**
- `draft` — generated, not yet acted on (default)
- `published` — user has posted it; user fills in `published_text_snippet` (first 80 chars) and optionally `published_url`
- `skipped` — user chose not to post it

Status is updated manually by the user. No pipeline logic branches on it — it exists for the user's own tracking and for the review matching step.

### strategy.md

```markdown
# Content Strategy — Cycle N
Generated: YYYY-MM-DD | Next review: YYYY-MM-DD

## Voice & Tone
[derived from post analysis]

## Core Themes (ranked by past performance)
1. Theme A — high engagement
2. Theme B — medium engagement
3. Theme C — low engagement (deprioritize)

## Content Mix (per 8-week cycle)
- 40% thought leadership (contrarian takes)
- 30% behind-the-scenes / build-in-public
- 20% tactical how-tos
- 10% personal story

## Posting Cadence
3× per week — Mon / Wed / Fri

## What's Working
[from ratings + scrape data — empty on cycle 1]

## What to Avoid
[low performers, audience mismatches — empty on cycle 1]

## Industry Context
[web-researched trends used this cycle]
```

Cap: ~800 words to stay within Claude's context budget across all calls that include it.

### raw-posts.txt (manual fallback format)

Used when scraping fails. One post per block, blocks separated by `---`:

```
---
date: 2026-01-15
likes: 42
comments: 7
text:
This is the full text of the LinkedIn post.
It can span multiple lines.
---
date: 2026-01-10
likes: 18
comments: 2
text:
Another post here.
---
```

---

## Post Generation Prompt Composition

Before generating posts, `generator.py` pre-builds a **slot plan** — a list of 24 dicts, one per post:

```python
{"week": 1, "position": 1, "hook_type": "contrarian", "topic": "AI agents replacing PMs"}
```

Slot plan construction:
- Content mix percentages from `strategy.md` are converted to post counts: e.g. 40% contrarian → 10 posts, 30% behind-the-scenes → 7 posts, 20% how-to → 5 posts, 10% story → 2 posts (rounded to sum to 24)
- Hook types map to content-mix categories: `contrarian` → thought leadership, `behind-the-scenes` → build-in-public, `how-to` → tactical, `story` / `news-hook` → personal/timely
- Topics are assigned by Claude in a single pre-generation call: given the strategy + niche + current industry trends, Claude returns a JSON array of 24 `{hook_type, topic}` pairs. `generator.py` zips these with the week/position slots.
- Slot plan is written to `state/cycle-{N}/slot-plan.json` before generation begins — if generation is interrupted, the plan is reused on restart and only missing posts are generated.

Each of the 24 posts is then generated in a separate Claude call with:
- Full `state/strategy.md` (~800 words)
- 5 example posts from the user's scraped history (voice calibration — shortest 5 by token count)
- The web-fetched news snippet for this post's topic (`web.py.search(topic + " news this week")`, top result summary, max 200 words)
- The slot's `{week, position, hook_type, topic}` as the generation instruction

Claude also outputs a suggested `image_query` string alongside the post text. `web.py.image_search(image_query)` is called immediately after; it returns `{url, source_domain, photographer}` if available, or `null`. `image_credit` is set to `"Photo by {photographer} on {source_domain}"` if attribution fields are present, otherwise `null`.

---

## web.py — Openclaw Usage

`web.py` is the single interface to all external web data. All calls include retry logic (3 attempts, exponential backoff). On final failure, the calling module receives `None` and handles gracefully.

| Module | Call | Purpose |
|---|---|---|
| `run.py` (init step 1) | `fetch(landing_page_url)` | Parse user's services and positioning |
| `analyzer.py` | `search(niche + " LinkedIn trends")` | Industry trend research |
| `analyzer.py` | `search("top LinkedIn influencers " + niche)` | Competitor post benchmarking |
| `generator.py` | `search(topic + " news this week")` | Current events hook per post |
| `generator.py` | `image_search(claude_image_query)` | Image per post |

**`niche`** is passed as a required `--niche` CLI argument on `init` and stored in `state/niche.txt` for reuse by `generate` and `review`.

**`image_search` return schema:**
```python
{
  "url": "https://...",
  "source_domain": "unsplash.com",
  "photographer": "Jane Doe"   # or None
}
```
Returns `None` if no results found — post frontmatter gets `image_url: null`, `image_credit: null`, flagged with a `# MANUAL` comment on those lines.

> **Note:** The exact Openclaw package name and API surface must be verified before implementation begins. The method names (`fetch`, `search`, `image_search`) and return shapes above are the intended interface; `web.py` will adapt them to the actual SDK once confirmed.

---

## Playwright Scraping Details

Both `init` and `review` scraping use **headed mode** (visible browser) with human-speed delays (500–1500ms randomized between actions) to reduce LinkedIn bot detection risk. The `state/.auth/linkedin.json` session is reused on `review` — the browser is visible but the user does not need to log in again unless the session has expired (in which case, Playwright pauses for re-login automatically).

---

## Error Handling

| Scenario | Behavior |
|---|---|
| LinkedIn scrape fails / DOM changed | Graceful error message + instructions to populate `state/raw-posts.txt` manually |
| Openclaw call fails after 3 retries | Field set to `null` with `# MANUAL` comment; pipeline continues |
| `run.py init` with existing `state/` | Exits with error; user must pass `--force` or delete `state/` |
| Image search returns no results | `image_url: null`, `image_credit: null`, `# MANUAL` flag |
| `review` rating session interrupted | Ratings already written to `review.md`; re-running skips rated posts |
| Unmatched post during review re-scrape | Listed in `review.md` as `status: not_found` — rated manually by user if desired |

---

## Auth Session

- On `init`, Playwright opens headed browser and pauses for user login (supports 2FA)
- Session saved to `state/.auth/linkedin.json`
- Reused on subsequent `scraper.py` calls
- `state/.auth/` is gitignored

---

## Environment Variables

```
ANTHROPIC_API_KEY=...
OPENCLAW_API_KEY=...
```

Loaded from `.env` in the project root (same pattern as `generate_page.py`).

---

## Dependencies

```
anthropic
playwright
openclaw   # package name TBC — verify before implementation
```
