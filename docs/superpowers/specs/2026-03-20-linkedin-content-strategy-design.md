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
├── strategist.py    # Claude + web.py: build and update strategy.md
├── generator.py     # Claude + web.py: generate 8-week post batch with news hooks + images
├── reviewer.py      # Playwright + Claude: collect engagement data + user ratings + re-strategize
└── web.py           # Openclaw wrapper: search, page fetch, image search
```

### State Layout

```
state/
├── .auth/           # Playwright saved auth session (not committed to git)
├── raw-posts.txt    # Manual fallback if scraper fails
├── strategy.md      # Current content strategy (updated each cycle)
├── cycle-01/
│   ├── week-01-post-1.md
│   ├── week-01-post-2.md
│   ├── week-01-post-3.md
│   └── ...          # 24 posts total (3/week × 8 weeks)
│   └── review.md    # Engagement data + user ratings after week 8
└── cycle-02/
    └── ...
```

---

## Three Modes

### `init` — First Run
```
python run.py init <landing_page_url> <linkedin_url>
```
1. `web.py` fetches and parses the landing page → extracts services, positioning, tone
2. `scraper.py` opens a visible Playwright browser → user logs into LinkedIn → auth session saved → scrapes last ~50 posts (text, date, likes, comments)
3. `analyzer.py` sends posts to Claude → extracts voice, recurring themes, cadence, gaps; calls `web.py` for industry trend search and competitor/influencer benchmarks
4. `strategist.py` sends landing page summary + analysis to Claude → writes `state/strategy.md`
5. `generator.py` generates 24 posts one at a time; each post: Claude writes text using strategy + voice examples + web-fetched news hook; `web.py` runs image search using Claude-suggested query → best result attached
6. Posts written to `state/cycle-01/week-XX-post-Y.md`

### `generate` — Next Cycle (no review)
```
python run.py generate
```
Reads existing `state/strategy.md` + latest cycle's review, generates next 24 posts into `state/cycle-0N/`.

### `review` — 8-Week Re-evaluation
```
python run.py review
```
1. `scraper.py` re-scrapes the user's LinkedIn profile → pulls like/comment counts for all posts from the current cycle
2. `reviewer.py` CLI: presents each post + its engagement stats, prompts user to rate 1–5
3. Claude synthesizes scraped data + ratings → identifies what worked and what didn't → updates `state/strategy.md`
4. Automatically calls `generate` to produce the next cycle

---

## Data Formats

### Post Markdown File
```markdown
---
week: 1
post: 2
topic: AI agents in product management
hook_type: contrarian
status: draft
image_url: https://...
image_credit: Unsplash / Photographer Name
image_query: "AI robot product manager office"
---

[post text here — LinkedIn-formatted, ready to copy-paste]

**Suggested hashtags:** #ProductManagement #AIAgents #BuildInPublic
```

### strategy.md Structure
```markdown
# Content Strategy — Cycle N
Generated: YYYY-MM-DD | Next review: YYYY-MM-DD

## Voice & Tone
[derived from post analysis]

## Core Themes (ranked by past performance)
1. Theme A — engagement level
2. Theme B — engagement level
3. Theme C — engagement level

## Content Mix (per 8-week cycle)
- 40% thought leadership (contrarian takes)
- 30% behind-the-scenes / build-in-public
- 20% tactical how-tos
- 10% personal story

## Posting Cadence
3× per week — Mon / Wed / Fri

## What's Working
[from ratings + scrape data]

## What to Avoid
[low performers, audience mismatches]

## Industry Context
[web-researched trends used this cycle]
```

---

## web.py — Openclaw Usage

`web.py` is the single interface to all external web data. Used by:

| Module | Openclaw call | Purpose |
|---|---|---|
| `strategist.py` | `fetch(landing_page_url)` | Parse user's services and positioning |
| `analyzer.py` | `search(niche + "LinkedIn trends")` | Industry trend research |
| `analyzer.py` | `search(top influencers in niche)` | Competitor post benchmarking |
| `generator.py` | `search(topic + "news this week")` | Current events hook per post |
| `generator.py` | `image_search(claude_query)` | Image per post |

---

## Error Handling

| Scenario | Behavior |
|---|---|
| LinkedIn DOM change / scrape failure | Graceful error + fallback: user pastes posts into `state/raw-posts.txt` |
| Openclaw call fails | 3 retries with exponential backoff; on final failure, field left null with a `# MANUAL` comment in the markdown |
| `run.py init` with existing state | Exits with error; user must pass `--force` or delete `state/` |
| Image search returns no results | `image_url: null` — post flagged, user fills in manually |
| Claude token limit | Posts generated one at a time; strategy.md capped at ~800 words |

---

## Auth Session

- On first `init`, Playwright opens a visible browser and pauses for the user to complete LinkedIn login (including 2FA if enabled)
- Session saved to `state/.auth/linkedin.json`
- Reused on all subsequent `scraper.py` calls — no re-login required unless session expires
- `state/.auth/` added to `.gitignore`

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
openclaw  # (to be verified — may be openclaw-sdk or similar)
```
