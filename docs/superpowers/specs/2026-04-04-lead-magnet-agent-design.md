# Lead Magnet Agent — Design Spec
Date: 2026-04-04

## Overview

A CLI agent that helps senior consultants create high-value lead magnets (white papers, mini-apps, datasets) to grow their audience. Given a consultant's landing page URL, the agent researches their niche, brainstorms lead magnet concepts across all three formats, critiques and prioritises them by impact vs. effort, surfaces the best idea for consultant approval, then generates the final artifact.

---

## Architecture

### Module Layout

```
lead_magnet_agent/
├── run.py           # CLI orchestrator: init | plan | generate
├── researcher.py    # fetches URL, searches web, reads past content from state
├── planner.py       # brainstorms concepts across formats, runs critique loop, ranks by impact/effort
├── writer.py        # format-aware artifact generator with per-section critique
├── web.py           # thin wrapper — reuses linkedin_agent/web.py (not duplicated)
└── __init__.py
```

### State Directory Layout

Created by `init`, populated progressively:

```
state/
├── profile.md           # consultant profile extracted from landing page URL
├── niche.txt            # consultant's niche label
├── url.txt              # source URL
├── content/             # past lead magnets manually added by consultant
│   └── <slug>/
│       ├── asset.*      # the artifact (HTML, CSV, PDF, etc.)
│       ├── meta.json    # { title, format, date, topic }
│       └── impact.json  # { downloads, leads_generated, notes }
├── plans/
│   ├── <slug>-plan.json        # approved plan, consumed by generate
│   └── <slug>-critique-log.md # internal critique rounds log
└── output/
    └── <slug>/
        ├── plan.json    # copy of the plan used
        ├── outline.md   # section outline (doc/dataset only)
        ├── artifact.*   # final deliverable
        └── critique.md  # writer self-critique log
```

---

## CLI Modes

### `init <url> --niche <label>`
- Fetches the URL via `WebClient`
- Extracts a consultant profile (name, positioning, audience, expertise) via Claude
- Saves `profile.md`, `niche.txt`, `url.txt`
- Creates the full state directory structure

### `plan [--topic-hint "..."]`
- Runs `researcher.py` → `planner.py`
- Surfaces the winning concept as a **concept card** printed to stdout:
  ```
  Format:   mini-app
  Title:    "The AI Marketing Audit Tool"
  Audience: Senior marketing consultants
  Angle:    Interactive self-assessment that scores their team's AI readiness
  Why it wins: High perceived value, zero marginal cost to distribute, strong email-gate pull
  Impact score: 8/10  |  Effort score: 4/10
  ```
- Saves concept card + full plan to `plans/<slug>-plan.json`
- **Pauses here.** Consultant reviews and runs `generate <slug>` when ready.

### `generate <slug>`
- Loads `plans/<slug>-plan.json`
- Runs `writer.py` in the appropriate format mode
- Saves final artifact + critique log to `output/<slug>/`

---

## Data Flow

### Research Phase (`researcher.py`)

Produces an in-memory `research_brief` dict:

```python
{
  "profile_summary": str,        # from profile.md
  "past_content": [...],         # from content/*/meta.json + impact.json
  "web_findings": [...],         # 3-5 web search results
  "niche": str
}
```

Web searches run 3-5 queries covering: niche trends, competitor lead magnets, and audience pain points. Uses the shared `WebClient` from `linkedin_agent/web.py`.

### Planning Phase (`planner.py`)

1. **Brainstorm:** Generate N ideas (typically 6-9) spread across `doc`, `dataset`, and `app` formats, grounded in the research brief.
2. **Score:** Each idea is scored on:
   - `impact` (1-10): audience fit, uniqueness, download pull
   - `effort` (1-10): complexity to produce (lower = easier)
3. **Rank:** Sort by `impact - effort * 0.5`. Take top 3.
4. **Critique loop (max 5 rounds):** A separate Claude call plays devil's advocate on the top-ranked idea:
   - Prompt: *"Would a senior [niche] consultant's prospect pay with their email for this? Score 1-10 and explain why not."*
   - If score ≥ 7: converge and exit loop early.
   - If score < 7: refine the idea using the critic's objections as constraints, re-score.
   - After 5 rounds: take the highest-scoring version regardless.
5. **Output:** Final `plan.json` + `critique-log.md`

### Writing Phase (`writer.py`)

Dispatches by format:

**`doc` (white paper / guide):**
- `brainstorm_outline()` → 5-7 section titles + one-line purpose each
- `critique_outline()` → single pass: is the flow logical? does it deliver the core promise?
- For each section: `write_section()` → `critique_section()` (pass/fail + one fix) → apply fix → finalize
- Renders to a styled self-contained HTML file (always HTML — consistent with app/dataset output and easier to distribute as a download)

**`dataset`:**
- `generate_dataset()` → structured JSON/CSV with research-backed data
- `generate_viz_page()` → companion self-contained HTML page with charts/tables
- Single critic pass on the dataset for accuracy and credibility

**`app` (mini-app):**
- `write_app()` → self-contained HTML/JS interactive tool in one generation pass
- `critique_app()` → single critic pass: does it deliver the promised value? is the UX clear?
- Apply fix and finalize

---

## Key Design Decisions

- **Shared `web.py`:** `lead_magnet_agent/web.py` is a thin re-export of `linkedin_agent.web.WebClient`. If the two agents are ever decoupled into separate packages, `web.py` should be extracted to a shared `common/` module. For now, the import is `from linkedin_agent.web import WebClient`.
- **Pause between plan and generate:** The approval checkpoint is enforced by the CLI — `generate` only works if a `plan.json` exists in `plans/`. There is no auto-advance.
- **App generation is holistic:** Unlike docs (section-by-section critique), apps are written and critiqued as a whole artifact.
- **Past content as signal:** The `content/` directory is populated manually by the consultant over time. The researcher reads `impact.json` to learn what has historically driven leads, feeding this as prior knowledge into the brainstorm.

---

## Improvement Areas

1. **Dynamic critique threshold:** The critique loop currently has a hard cap of 5 rounds. A stronger approach would be to exit early when score ≥ 7 (already implemented) but also allow the loop to continue beyond 5 if the score is still very low (e.g., < 4), with a hard stop at 10. The cap is a pragmatic constraint, not an ideal one.
2. **Multi-idea surfacing:** Currently the agent surfaces one winning idea. A future mode could surface the top 3 with trade-offs and let the consultant choose.
3. **Automated impact tracking:** `impact.json` is populated manually. A future integration with the consultant's landing page analytics (e.g., via a webhook or download counter) would close the feedback loop automatically.
4. **Dataset sourcing:** For `dataset` format, the agent currently synthesises data from web search results. Real datasets from public APIs (e.g., industry reports, government data) would significantly increase credibility.
5. **App testing:** Generated HTML/JS apps are not programmatically tested. A headless browser validation step (Playwright) could catch broken JS before delivery.
