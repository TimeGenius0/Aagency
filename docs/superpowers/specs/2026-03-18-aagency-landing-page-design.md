# Aagency.ai Landing Page — Design Spec

**Date:** 2026-03-18
**Status:** Approved for implementation

---

## Overview

A single-page marketing site for **Aagency.ai** — a platform that turns senior professionals (C-suite executives and domain specialists) into AI-powered agency owners. The design is dark, minimal, and editorial, inspired by intro.com. The primary conversion action is **booking a 15-minute discovery call**.

---

## Visual Identity

- **Background:** Near-black (`#080808`)
- **Off-black:** `#0e0e0e` (used for card interiors)
- **Borders:** `#1a1a1a` (standard), `#242424` (light variant)
- **Text:** `#f0f0f0` (primary), `#888` (secondary), `#444` (muted)
- **White:** `#ffffff`
- **Typography:** Georgia/serif for headlines and numbers; `-apple-system, 'Inter', 'Helvetica Neue', sans-serif` for body and UI
- **Max content width:** `1200px`, centered, with `60px` side padding
- **Tone:** Exclusive, prestigious, confident — like a private members club for top operators
- **Logo:** Italic serif wordmark "Aagency.ai" with a rotating `✦` star (see Logo section below)

### Logo

The `✦` star sits to the left of the italic wordmark. Animations:
- **Rotation:** 5s linear infinite (`0° → 360°`), scales to `1.18×` at 90° and 270° midpoints
- **Color cycle:** 8s ease-in-out infinite, cycling through these **7 stops**: `#ffffff → #a78bfa → #60a5fa → #34d399 → #f472b6 → #fb923c → #818cf8 → #ffffff`
- **Glow:** `text-shadow` matches current color at `0.6` opacity, radius `12px`
- Star font-size: `17px` in nav, `11px` in footer

---

## Tech Stack

- Plain HTML + CSS + vanilla JS (no framework, no build step)
- Single `index.html` file
- Images via Unsplash CDN (placeholder — to be replaced with real photos)
- Calendly embed for booking widget (mock slot-picker in v1)

---

## Page Structure & Section IDs

| # | Section | `id` attribute |
|---|---|---|
| 1 | Navigation (fixed) | `#nav` |
| 2 | Hero | `#hero` |
| 3 | Social Proof | `#proof` |
| 4 | How It Works | `#how-it-works` |
| 5 | The Model | `#the-model` |
| 6 | Who It's For | `#who` |
| 7 | Book a Call | `#book` |
| 8 | Footer | `#footer` |

Nav links map: "How it works" → `#how-it-works`, "Who it's for" → `#who`, "Book a call" → `#book`.

---

## Sections

### 1. Navigation (fixed)

- Fixed to top, full width, `z-index: 100`
- Padding: `24px 60px`
- Border-bottom: `1px solid #1a1a1a`
- Background: `rgba(8,8,8,0.92)` + `backdrop-filter: blur(12px)`
- Logo left, nav links right: "How it works", "Who it's for", then "Book a call" styled as a bordered CTA button (`border: 1px solid #242424`, `padding: 8px 20px`, uppercase `11px` with `1.5px` letter-spacing)

---

### 2. Hero

**Layout:** Two implicit regions. Left 58% contains the editorial text content pinned to the bottom-left. Right 42% is the photo mosaic — an absolutely positioned element filling the full section height from `top: 0, right: 0`.

- Section: `min-height: 100vh`, `padding: 160px 60px 100px`, flex column, `justify-content: flex-end`
- **Stats bar:** Absolutely positioned at `right: 60px, bottom: 100px`, flex column, right-aligned

#### Photo mosaic

- Position: `absolute`, `top: 0`, `right: 0`, `width: 42%`, `height: 100%`
- Grid: `3 columns × 4 rows`, `gap: 2px`
- Cell aspect ratio: each cell fills its grid area naturally (no forced aspect ratio needed — the grid rows divide the full height equally)
- Overlay gradient (pseudo-element `::after`, `z-index: 1`, pointer-events none):
  - `linear-gradient(to right, #080808 0%, transparent 40%)` — fades left edge into background
  - `linear-gradient(to top, #080808 0%, transparent 30%)` — fades bottom edge
- Load animation: `opacity: 0 → 0.35`, `scale(1.04) → scale(1)`, duration `1.4s`, delay `0.3s`, ease
- Mouse parallax: translates `±14px` on X and `±10px` on Y relative to viewport center; `transition: transform 0.6s cubic-bezier(0.16,1,0.3,1)`

#### Photo cell hover (each cell is a wrapper `<div class="photo-cell">`)

Each cell has a unique CSS custom property `--cell-color` and a matching background for the `::before` color overlay. On hover:
- **Image:** `filter: grayscale(0%) brightness(1.05)`, `transform: scale(1.07)`, transition `0.5s`
- **`::before` overlay:** `opacity: 0 → 0.55`, `mix-blend-mode: color`, background = `--cell-color`
- **`::after` border+glow:** `box-shadow: inset 0 0 0 4px var(--cell-color), inset 0 0 28px rgba(0,0,0,0.3), 0 0 30px var(--cell-color)`

Color assignments (12 cells, `nth-child` order):
`#a78bfa, #60a5fa, #34d399, #f472b6, #fb923c, #818cf8, #2dd4bf, #e879f9, #facc15, #4ade80, #f87171, #38bdf8`

#### Cursor glow

- A `<div id="cursorGlow">` inside the hero section, `position: absolute`, `pointer-events: none`, `z-index: 1`
- Size: `500px × 500px`, centered on cursor via `transform: translate(-50%, -50%)`, `left` and `top` set by JS
- Background: `radial-gradient(circle, rgba(R,G,B,0.07) 0%, transparent 65%)`
- Default color when no cell is hovered: `rgba(255,255,255,0.07)`
- On cell hover: color transitions to match `--cell-color` of the hovered cell; size expands to `600px × 600px`
- Fades out (`opacity: 0`) when mouse leaves the hero section; `transition: opacity 0.4s`
- The glow tracks the actual cursor position (not the cell center)

#### Headline entrance animation

Three `<span class="line">` elements inside `<h1>`. Each animates from `opacity: 0, translateY(40px)` to `opacity: 1, translateY(0)` using `cubic-bezier(0.16,1,0.3,1)`, duration `0.9s`:
- Line 1: delay `0.7s`
- Line 2: delay `0.85s`
- Line 3: delay `1.0s`

Eyebrow, subtext, and actions: `opacity: 0, translateY(12px) → opacity: 1, translateY(0)`, `0.8s ease`, delays `0.5s`, `1.15s`, `1.35s` respectively. Stats bar: delay `1.6s`.

#### Stat counters

Two figures: `$4,200` and `3 hrs`. Both animate from `0` using ease-out-expo over `1800ms`, triggered `1.9s` after page load (after stats bar fade-in completes). Format: integer only (no decimals). `$4,200` displays comma-separated. `3 hrs` appends ` hrs` suffix.

#### CTA button

- On hover: white fill slides in from left via `::before` pseudo-element, `transform: translateX(-101%) → translateX(0)`, `0.3s cubic-bezier(0.16,1,0.3,1)`. Text color transitions to black.
- Magnetic: tracks cursor when within `80px` of button center. Max displacement: `±12px` X, `±10px` Y. On mouse leave: resets to `translate(0,0)` with `transition: transform 0.4s ease`.
- Active state: `transform: scale(0.97)`

---

### 3. Social Proof (`#proof`)

- Section label: `"Early agency owners"` (uppercase, `10px`, `4px` letter-spacing, `#444`)
- 3 cards in a CSS grid, `1px` gaps, `background: #1a1a1a` on the grid container (creates divider lines)
- Each card `background: #080808`, `padding: 48px 40px`
- Card structure (top to bottom):
  1. Italic serif quote (`17px`, `#f0f0f0`)
  2. Row: circular avatar (`44px` diameter, `border-radius: 50%`, `filter: grayscale(30%)`) + name (`13px`, `#fff`) + title (`11px`, `#444`)
  3. Earnings block (separated by `1px` border-top): bold serif number + description text

Placeholder content:
- Sarah M., Former CMO · Series C SaaS — `$18,400 last month · 4.2 hrs invested`
- David K., Former Partner · IP Law Firm — `$31,000 last month · 7.5 hrs invested`
- Priya T., Former VP Engineering · Unicorn — `$22,600 last month · 5.1 hrs invested`

---

### 4. How It Works (`#how-it-works`)

- 2-column grid, `1fr 1fr`, `gap: 80px`
- Left: serif headline + supporting paragraph
- Right: 3 numbered steps, each separated by `1px solid #1a1a1a` border, `padding: 36px 0`
  - Step number: Georgia serif, `13px`, `#444`
  - Step title: `15px`, `#fff`, `font-weight: 500`
  - Step description: `13px`, `#888`

Steps:
1. **We find your clients** — Aagency matches your domain expertise to inbound client requests.
2. **AI agents deliver the work** — Coordinated AI agents produce strategies, documents, and deliverables.
3. **You review, validate, and earn** — Apply your judgment to approve the work. Meet the client. Every hour is multiplied.

---

### 5. The Model (`#the-model`)

#### Top half: 2-column copy + contrast box

Left column: editorial copy explaining core concept (reputation attracts, AI executes, expert approves).

Right column: two stacked boxes:
- "Without Aagency" box: `border: 1px solid #1a1a1a`, `background: #0e0e0e`, muted text
- "With Aagency" box: `border: 1px solid #ffffff`, `background: #0e0e0e`, a small white label badge positioned at the top-right of the border, normal text

#### Bottom half: Marcus diagram

Full-width panel (`border: 1px solid #1a1a1a`, `background: #0e0e0e`, `padding: 60px`).

**Top row (instruction flow):**
- Marcus L. avatar (72px circle, white 2px border, checkmark badge) + name/title/role badge
- Arrow line → "gives direction" label → instruction quote bubble → arrow line → "dispatched to" label → "12 min" time badge

**AI Agents row:**
- Label: `"AI Agents — working in parallel"`
- 5 cards in a 5-column grid: Research Agent, Copy Agent, Planning Agent, Analytics Agent, Visual Agent
- Each card: emoji icon, agent name, task description, status badge
- Status badges: `RUNNING` (green `#22c55e`), `REVIEWING` (amber `#f59e0b`), `QUEUED` (gray `#6b7280`)
- **Status badges are static in v1** — no auto-cycling animation

**Human specialists row:**
- Label: `"Human specialists — refining output"`
- 3 cards in a row: Brand Strategist, Media Specialist, Data Analyst — each with a 32px circular headshot, name, and current task

**Output bar (bottom of diagram):**
- Left: deliverable title + description
- Center: "45 min — Marcus reviews & approves"
- Right (separated by `1px` border-left): "Billed to client" label + `$24,000` in large Georgia serif

---

### 6. Who It's For (`#who`)

2-column card grid (`1px` gap dividers):
- Card 1: C-Suite Executives — icon, title, description, tags: CMO, CFO, COO, CTO, CEO
- Card 2: Senior Domain Specialists — icon, title, description, tags: Lawyers, Engineers, Designers, Advisors

Full-width card spanning both columns (off-black background), 2-column interior:
- Left: "You're the right fit if…" — 4 bullet points (15+ years experience, earn on own terms, open to AI, quality over volume)
- Right: "This is not for you if…" — 3 disqualifiers (early career, want traditional consulting, uncomfortable with AI)

---

### 7. Book a Call (`#book`)

2-column split, `gap: 80px`, vertically centered:

**Left:** editorial headline ("15 minutes. That's all it takes to find out.") + supporting paragraph + 4-item checklist (dashes as bullets) + CTA copy

**Right:** mock slot picker panel (`background: #0e0e0e`, `border: 1px solid #1a1a1a`, `padding: 40px`):
- Header: "Book a discovery call · 15 min"
- 4 time slots as selectable rows (`border: 1px solid #1a1a1a`), hover state: border brightens to `#888`, color to `#fff`
- Selected state: `border: 1px solid #ffffff`, white text
- Default selected: first slot
- "Confirm this time →" button: full-width, `background: #ffffff`, `color: #080808`, uppercase `11px`
- **Post-click state:** button changes to `"✓ Confirmed — check your email"`, background `#1a1a1a`, text `#888`, non-interactive (pointer-events: none). No other UI changes in v1.

---

### 8. Footer

- `padding: 60px`
- Left: animated logo (smaller star `11px`, italic wordmark `16px`, muted gray)
- Right: `"© 2026 · Invite only · All rights reserved"`, `11px`, `#444`

---

## Animations Summary

| Element | Trigger | Behavior |
|---|---|---|
| Logo star | Always | Rotate 5s linear; color cycle 8s through 7 colors with glow |
| Hero photo grid | Page load | Fade in (`0 → 0.35 opacity`) + scale down (`1.04 → 1`), 1.4s, delay 0.3s |
| Hero photo grid | Mouse move in hero | Parallax ±14px X / ±10px Y, spring ease 0.6s |
| Photo cell | Hover | Desaturate lifts, color tint overlay, 4px inset border, outer glow — unique color per cell |
| Cursor glow | Mouse move in hero | 500px radial follows cursor; color matches hovered cell; expands to 600px on cell hover |
| Hero eyebrow | Page load | Fade + translateY(12px→0), 0.8s, delay 0.5s |
| Hero headline | Page load | Each line slides up from translateY(40px), staggered 0.15s, spring ease 0.9s |
| Hero sub + actions | Page load | Fade + translateY, cascading delays 1.15s / 1.35s |
| Stats bar | Page load | Fade in, delay 1.6s |
| Stat counters | 1.9s after load | Count 0→target, ease-out-expo, 1800ms |
| CTA button | Hover | White fill slides in from left, 0.3s spring ease |
| CTA button | Cursor proximity (80px) | Magnetic pull max ±12px X / ±10px Y |
| CTA button | Active | scale(0.97) |
| Section entries | Scroll into view | `IntersectionObserver` threshold `0.15`; `opacity: 0, translateY(24px) → opacity: 1, translateY(0)`; duration `0.7s ease`; no child staggering in v1 |
| Slot picker confirm | Click | Button → "✓ Confirmed — check your email", grayed out, non-interactive |

---

## Out of Scope (v1)

- Mobile responsive layout
- Backend / form submission / real Calendly integration
- Authentication or gating
- Analytics integration
- Multi-page routing
- Keyboard accessibility (to be addressed post-v1)
- Ultra-wide (>1440px) layout — max content width `1200px` centered prevents unbounded stretching
