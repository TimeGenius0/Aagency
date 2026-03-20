# Aagency.ai Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the production `index.html` for Aagency.ai — a single-file dark editorial landing page with rich animations, a hero photo mosaic, and a mock booking flow.

**Architecture:** Single `index.html` containing all HTML, CSS (in a `<style>` block), and JS (in a `<script>` block before `</body>`). No build step, no dependencies, no frameworks. Images served from Unsplash CDN. The approved design mockup lives at `.superpowers/brainstorm/12156-1773886284/full-mockup.html` and is the canonical visual reference — implement to match it exactly.

**Tech Stack:** HTML5, CSS3 (custom properties, conic-gradient, clip-path, IntersectionObserver), vanilla JS (no libraries)

---

## Reference Files

- **Spec:** `docs/superpowers/specs/2026-03-18-aagency-landing-page-design.md`
- **Visual reference (approved mockup):** `.superpowers/brainstorm/12156-1773886284/full-mockup.html`
- **Output:** `index.html` (project root)

---

## File Structure

```
/home/bilelburaway/dev/Aagency/
├── index.html          ← single output file (create)
├── .gitignore          ← create
└── docs/
    └── superpowers/
        ├── specs/      ← existing
        └── plans/      ← existing
```

---

## Task 1: Project Setup

**Files:**
- Create: `.gitignore`
- Create: `index.html` (skeleton only)

- [ ] **Step 1: Initialise git**

```bash
cd /home/bilelburaway/dev/Aagency
git init
```

- [ ] **Step 2: Create `.gitignore`**

```
.superpowers/
.DS_Store
*.log
```

- [ ] **Step 3: Create `index.html` skeleton**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aagency.ai — Turn your expertise into an agency</title>
<style>
/* styles go here */
</style>
</head>
<body>
<!-- content goes here -->
<script>
// scripts go here
</script>
</body>
</html>
```

- [ ] **Step 4: Verify file opens in browser without errors**

Open `index.html` in browser. Expect: blank page, no console errors.

- [ ] **Step 5: Commit**

```bash
git add .gitignore index.html
git commit -m "chore: project setup and index.html skeleton"
```

---

## Task 2: CSS — Design Tokens & Base Styles

**Files:**
- Modify: `index.html` (CSS `<style>` block)

- [ ] **Step 1: Add CSS reset and custom properties**

Inside `<style>`, add:

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --black: #080808;
  --off-black: #0e0e0e;
  --border: #1a1a1a;
  --border-light: #242424;
  --text-primary: #f0f0f0;
  --text-secondary: #888;
  --text-muted: #444;
  --white: #ffffff;
}

body {
  background: var(--black);
  color: var(--text-primary);
  font-family: -apple-system, 'Inter', 'Helvetica Neue', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
```

- [ ] **Step 2: Add section base styles**

```css
section { border-bottom: 1px solid var(--border); }

.section-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 100px 60px;
}
```

- [ ] **Step 3: Verify in browser**

Expect: black background, no visible content yet, no console errors.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "style: design tokens and base reset"
```

---

## Task 3: CSS — Logo Star Animation

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add logo CSS**

```css
.nav-logo {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 19px;
  color: var(--white);
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  gap: 7px;
  font-weight: normal;
}
.nav-logo-text { display: flex; align-items: baseline; }
.nav-logo-name { font-style: italic; letter-spacing: -0.5px; }
.nav-logo-tld  { color: var(--text-secondary); font-style: normal; font-size: 15px; }

.nav-logo-star {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  line-height: 1;
  animation: star-spin 5s linear infinite, star-color 8s ease-in-out infinite;
  transform-origin: center;
}

@keyframes star-spin {
  0%   { transform: rotate(0deg)   scale(1);    }
  25%  { transform: rotate(90deg)  scale(1.18); }
  50%  { transform: rotate(180deg) scale(1);    }
  75%  { transform: rotate(270deg) scale(1.18); }
  100% { transform: rotate(360deg) scale(1);    }
}

@keyframes star-color {
  0%   { color: #ffffff; text-shadow: 0 0 8px rgba(255,255,255,0.4); }
  14%  { color: #a78bfa; text-shadow: 0 0 12px rgba(167,139,250,0.6); }
  28%  { color: #60a5fa; text-shadow: 0 0 12px rgba(96,165,250,0.6); }
  42%  { color: #34d399; text-shadow: 0 0 12px rgba(52,211,153,0.6); }
  57%  { color: #f472b6; text-shadow: 0 0 12px rgba(244,114,182,0.6); }
  71%  { color: #fb923c; text-shadow: 0 0 12px rgba(251,146,60,0.6); }
  85%  { color: #818cf8; text-shadow: 0 0 12px rgba(129,140,248,0.6); }
  100% { color: #ffffff; text-shadow: 0 0 8px rgba(255,255,255,0.4); }
}
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "style: logo star spin and colour-cycle animation"
```

---

## Task 4: CSS — Navigation

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add nav styles**

```css
nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 60px;
  border-bottom: 1px solid var(--border);
  background: rgba(8,8,8,0.92);
  backdrop-filter: blur(12px);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 40px;
}

.nav-links a {
  font-size: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  letter-spacing: 0.5px;
  position: relative;
}

.nav-links a::after {
  content: '';
  position: absolute;
  bottom: -4px; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399, #f472b6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.35s cubic-bezier(0.16,1,0.3,1);
}

.nav-links a:not(.nav-cta):hover { color: var(--white); }
.nav-links a:not(.nav-cta):hover::after { transform: scaleX(1); }

.nav-cta {
  font-size: 11px;
  color: var(--white) !important;
  border: 1px solid var(--border-light) !important;
  padding: 8px 20px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  transition: border-color 0.2s;
}
```

- [ ] **Step 2: Add nav HTML**

```html
<nav id="nav">
  <div class="nav-logo">
    <span class="nav-logo-star">✦</span>
    <div class="nav-logo-text">
      <span class="nav-logo-name">Aagency</span><span class="nav-logo-tld">.ai</span>
    </div>
  </div>
  <div class="nav-links">
    <a href="#how-it-works">How it works</a>
    <a href="#who">Who it's for</a>
    <a href="#book" class="nav-cta">Book a call</a>
  </div>
</nav>
```

- [ ] **Step 3: Verify in browser**

Expect: fixed dark nav at top, animated star, rainbow underline on link hover.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: navigation with logo star and rainbow hover underlines"
```

---

## Task 5: CSS — Wild Border Animation System

**Files:**
- Modify: `index.html`

Copy the full wild-border CSS block from the mockup. This is referenced by `.wild-hover` and `.wild-hover-sm` throughout the page.

- [ ] **Step 1: Add wild-border CSS**

```css
.wild-hover { transition: box-shadow 0.3s; }
.wild-hover:hover { animation: wild-glow 3.5s ease-in-out infinite; }
.wild-hover-sm:hover { animation: wild-glow-sm 3s ease-in-out infinite; }

@keyframes wild-glow {
  0%   { box-shadow: -6px -4px 0 4px #a78bfa,  5px -3px 0 3px #60a5fa,  5px  7px 0 6px #34d399, -4px  5px 0 4px #f472b6, 0 0 36px 6px rgba(167,139,250,0.45); }
  20%  { box-shadow: -4px -8px 0 3px #f472b6,  8px -4px 0 6px #a78bfa,  3px  5px 0 4px #fb923c, -8px  3px 0 5px #34d399, 0 0 36px 6px rgba(244,114,182,0.45); }
  40%  { box-shadow: -9px -3px 0 6px #60a5fa,  3px -9px 0 4px #e879f9,  9px  4px 0 3px #facc15, -3px  9px 0 6px #818cf8, 0 0 36px 6px rgba(96,165,250,0.45); }
  60%  { box-shadow: -5px -7px 0 4px #34d399,  7px -4px 0 5px #fb923c,  4px  7px 0 5px #a78bfa, -7px  4px 0 3px #2dd4bf, 0 0 36px 6px rgba(52,211,153,0.45); }
  80%  { box-shadow: -8px -4px 0 5px #e879f9,  4px -7px 0 3px #facc15,  7px  3px 0 4px #38bdf8, -4px  8px 0 5px #fb923c, 0 0 36px 6px rgba(232,121,249,0.45); }
  100% { box-shadow: -6px -4px 0 4px #a78bfa,  5px -3px 0 3px #60a5fa,  5px  7px 0 6px #34d399, -4px  5px 0 4px #f472b6, 0 0 36px 6px rgba(167,139,250,0.45); }
}

@keyframes wild-glow-sm {
  0%   { box-shadow: -4px -3px 0 3px #a78bfa, 3px -2px 0 2px #60a5fa, 3px 4px 0 4px #34d399, -3px 3px 0 3px #f472b6, 0 0 20px 4px rgba(167,139,250,0.5); }
  20%  { box-shadow: -3px -5px 0 2px #f472b6, 5px -3px 0 4px #a78bfa, 2px 3px 0 3px #fb923c, -5px 2px 0 3px #34d399, 0 0 20px 4px rgba(244,114,182,0.5); }
  40%  { box-shadow: -5px -2px 0 4px #60a5fa, 2px -5px 0 3px #e879f9, 5px 3px 0 2px #facc15, -2px 5px 0 4px #818cf8, 0 0 20px 4px rgba(96,165,250,0.5); }
  60%  { box-shadow: -3px -4px 0 3px #34d399, 4px -3px 0 3px #fb923c, 3px 4px 0 3px #a78bfa, -4px 3px 0 2px #2dd4bf, 0 0 20px 4px rgba(52,211,153,0.5); }
  80%  { box-shadow: -5px -3px 0 3px #e879f9, 3px -4px 0 2px #facc15, 4px 2px 0 3px #38bdf8, -3px 5px 0 3px #fb923c, 0 0 20px 4px rgba(232,121,249,0.5); }
  100% { box-shadow: -4px -3px 0 3px #a78bfa, 3px -2px 0 2px #60a5fa, 3px 4px 0 4px #34d399, -3px 3px 0 3px #f472b6, 0 0 20px 4px rgba(167,139,250,0.5); }
}
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "style: wild-border reusable animation system"
```

---

## Task 6: CSS — Scroll Reveal & Section Label Shimmer

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add scroll-reveal CSS**

```css
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}
.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}
```

- [ ] **Step 2: Add section-label shimmer**

```css
.section-label {
  font-size: 10px;
  letter-spacing: 4px;
  text-transform: uppercase;
  margin-bottom: 60px;
  display: flex;
  align-items: center;
  gap: 16px;
  background: linear-gradient(90deg,
    var(--text-muted) 0%, var(--text-muted) 20%,
    #a78bfa 35%, #60a5fa 42%, #34d399 50%,
    var(--text-muted) 65%, var(--text-muted) 100%
  );
  background-size: 250% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: label-shimmer 6s linear infinite;
}

@keyframes label-shimmer {
  0%   { background-position: 100% center; }
  100% { background-position: -100% center; }
}

.section-label::after {
  content: '';
  display: block;
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border), transparent);
}
```

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "style: scroll-reveal and section-label shimmer animation"
```

---

## Task 7: Hero Section — HTML + CSS

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add hero CSS**

Copy from mockup all CSS under `/* ─── HERO ─── */` through `/* ─── HERO TEXT ANIMATIONS ─── */` including:
- `.hero`, `.cursor-glow`, `.hero-photo-grid`, `.photo-cell` and all its states, `@keyframes grid-fade-in`, `@keyframes hero-line`, `@keyframes hero-in`, `.hero-eyebrow`, `.hero-headline`, `.hero-headline .line`, `.hero-sub`, `.hero-actions`, `.btn-primary` (including `::before` fill, hover, magnetic states), `.hero-note`, `.hero-stat-bar`, `.hero-stat`, `.hero-stat-num`, `.hero-stat-label`, photo cell nth-child colors and overlay backgrounds.

- [ ] **Step 2: Add hero HTML**

```html
<section class="hero" id="hero">
  <div class="cursor-glow" id="cursorGlow"></div>

  <div class="hero-photo-grid" id="photoGrid">
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=300&h=300&fit=crop&crop=face" alt=""></div>
    <div class="photo-cell"><img src="https://images.unsplash.com/photo-1504257432389-52343af06ae3?w=300&h=300&fit=crop&crop=face" alt=""></div>
  </div>

  <div class="hero-eyebrow">Invite only · AI-powered agency platform</div>
  <h1 class="hero-headline">
    <span class="line">Your expertise</span>
    <span class="line">is worth more</span>
    <span class="line">than your <em>time.</em></span>
  </h1>
  <p class="hero-sub">Aagency turns senior professionals into agency owners. We find the clients, AI agents do the work, you validate and earn — at a rate your career always deserved.</p>
  <div class="hero-actions">
    <a href="#book" class="btn-primary wild-hover-sm">Book a discovery call</a>
    <span class="hero-note">15 min · No commitment</span>
  </div>
  <div class="hero-stat-bar">
    <div class="hero-stat wild-hover-sm">
      <span class="hero-stat-num" data-count="4200" data-prefix="$" data-suffix="">$0</span>
      <span class="hero-stat-label">avg. per hour of owner time</span>
    </div>
    <div class="hero-stat wild-hover-sm">
      <span class="hero-stat-num" data-count="3" data-prefix="" data-suffix=" hrs">0 hrs</span>
      <span class="hero-stat-label">avg. weekly commitment</span>
    </div>
  </div>
</section>
```

- [ ] **Step 3: Verify in browser**

Expect: full-viewport hero, dark background, 3×4 photo mosaic fades in on right, headline lines slide up in sequence, stat bar appears. No console errors.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: hero section with photo mosaic and entrance animations"
```

---

## Task 8: JS — Hero Interactivity

**Files:**
- Modify: `index.html` (`<script>` block)

- [ ] **Step 1: Add cursor glow + photo parallax JS**

```js
// ── CURSOR GLOW ──
const hero = document.querySelector('.hero');
const glow = document.getElementById('cursorGlow');
let glowColor = '255,255,255';

hero.addEventListener('mousemove', e => {
  const rect = hero.getBoundingClientRect();
  glow.style.left = (e.clientX - rect.left) + 'px';
  glow.style.top  = (e.clientY - rect.top)  + 'px';
  glow.style.opacity = '1';
  glow.style.background = `radial-gradient(circle, rgba(${glowColor},0.07) 0%, transparent 65%)`;
});
hero.addEventListener('mouseleave', () => glow.style.opacity = '0');

// ── PHOTO CELL COLOUR SYNC ──
const colorMap = {
  1:'167,139,250', 2:'96,165,250', 3:'52,211,153', 4:'244,114,182',
  5:'251,146,60',  6:'129,140,248', 7:'45,212,191', 8:'232,121,249',
  9:'250,204,21',  10:'74,222,128', 11:'248,113,113', 12:'56,189,248'
};
document.querySelectorAll('.photo-cell').forEach((cell, i) => {
  const rgb = colorMap[i + 1] || '255,255,255';
  cell.addEventListener('mouseenter', () => {
    glowColor = rgb;
    glow.style.width = glow.style.height = '600px';
  });
  cell.addEventListener('mouseleave', () => {
    glowColor = '255,255,255';
    glow.style.width = glow.style.height = '500px';
  });
});

// ── PHOTO GRID PARALLAX ──
const grid = document.querySelector('.hero-photo-grid');
grid.style.transition = 'transform 0.6s cubic-bezier(0.16,1,0.3,1), opacity 0.4s';
hero.addEventListener('mousemove', e => {
  const dx = (e.clientX - window.innerWidth  / 2) / (window.innerWidth  / 2);
  const dy = (e.clientY - window.innerHeight / 2) / (window.innerHeight / 2);
  grid.style.transform = `translate(${dx * -14}px, ${dy * -10}px) scale(1.02)`;
});
hero.addEventListener('mouseleave', () => {
  grid.style.transform = 'translate(0,0) scale(1)';
});
```

- [ ] **Step 2: Add stat counters JS**

```js
// ── STAT COUNTERS ──
function animateCount(el) {
  const target = parseInt(el.dataset.count);
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const duration = 1800;
  const start = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(2, -10 * progress);
    el.textContent = prefix + Math.round(eased * target).toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
setTimeout(() => document.querySelectorAll('[data-count]').forEach(animateCount), 1900);
```

- [ ] **Step 3: Add magnetic CTA + scroll reveal JS**

```js
// ── MAGNETIC CTA (proximity-gated: only activates within 80px of button centre) ──
const btn = document.querySelector('.btn-primary');
const MAGNET_RADIUS = 80, MAX_X = 12, MAX_Y = 10;
document.addEventListener('mousemove', e => {
  const r = btn.getBoundingClientRect();
  const cx = r.left + r.width  / 2;
  const cy = r.top  + r.height / 2;
  const dx = e.clientX - cx;
  const dy = e.clientY - cy;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist < MAGNET_RADIUS) {
    const ratio = 1 - dist / MAGNET_RADIUS;
    btn.style.transform = `translate(${dx * ratio * (MAX_X / MAGNET_RADIUS) * 2}px, ${dy * ratio * (MAX_Y / MAGNET_RADIUS) * 2}px)`;
    btn.style.transition = 'transform 0.1s ease';
  } else {
    btn.style.transform = 'translate(0,0)';
    btn.style.transition = 'transform 0.4s ease';
  }
});

// ── SCROLL REVEAL ──
const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
```

- [ ] **Step 4: Verify in browser**

Expect: cursor glow tracks mouse in hero, photo grid subtly parallaxes, stats count up from 0 ~2s after load, CTA button has magnetic pull, sections fade in on scroll.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: hero JS — cursor glow, parallax, stat counters, magnetic CTA, scroll reveal"
```

---

## Task 9: Social Proof Section

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add proof section CSS**

Copy all CSS under `/* ─── SOCIAL PROOF ─── */` from mockup: `.proof-grid`, `.proof-card`, `.proof-quote`, `.proof-person`, `.proof-avatar`, `.proof-person-info`, `.proof-name`, `.proof-title`, `.proof-earnings`.

- [ ] **Step 2: Add proof section HTML**

```html
<section id="proof">
  <div class="section-inner">
    <div class="section-label">Early agency owners</div>
    <div class="proof-grid reveal">

      <div class="proof-card wild-hover">
        <p class="proof-quote">"I spent 20 years learning what great marketing looks like. Now I just say yes or no — and Aagency handles the rest. I've never felt more leveraged."</p>
        <div class="proof-person">
          <img class="proof-avatar" src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=88&h=88&fit=crop&crop=face" alt="Sarah M.">
          <div class="proof-person-info">
            <span class="proof-name">Sarah M.</span>
            <span class="proof-title">Former CMO · Series C SaaS</span>
          </div>
        </div>
        <div class="proof-earnings"><strong>$18,400</strong>earned last month · 4.2 hrs invested</div>
      </div>

      <div class="proof-card wild-hover">
        <p class="proof-quote">"As a retired IP attorney, I assumed my best earning years were behind me. Three months in, I'm billing more than my peak partner years — without the stress."</p>
        <div class="proof-person">
          <img class="proof-avatar" src="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=88&h=88&fit=crop&crop=face" alt="David K.">
          <div class="proof-person-info">
            <span class="proof-name">David K.</span>
            <span class="proof-title">Former Partner · IP Law Firm</span>
          </div>
        </div>
        <div class="proof-earnings"><strong>$31,000</strong>earned last month · 7.5 hrs invested</div>
      </div>

      <div class="proof-card wild-hover">
        <p class="proof-quote">"The AI does work that would have taken my team weeks. I review, refine, and approve. My experience is finally priced correctly."</p>
        <div class="proof-person">
          <img class="proof-avatar" src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=88&h=88&fit=crop&crop=face" alt="Priya T.">
          <div class="proof-person-info">
            <span class="proof-name">Priya T.</span>
            <span class="proof-title">Former VP Engineering · Unicorn</span>
          </div>
        </div>
        <div class="proof-earnings"><strong>$22,600</strong>earned last month · 5.1 hrs invested</div>
      </div>

    </div>
  </div>
</section>
```

- [ ] **Step 3: Verify in browser**

Expect: 3-column testimonial grid with avatars, earnings figures, wild-border on hover. Cards fade in on scroll.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: social proof section with testimonial cards"
```

---

## Task 10: How It Works Section

> **Note:** The spec describes 3 steps, but the user explicitly approved a 4-step version during brainstorming. The plan's 4-step content supersedes the spec. Follow the HTML below exactly.

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add how-it-works CSS**

Copy from mockup: `.how-layout`, `.how-headline`, `.how-sub`, `.steps`, `.step`, `.step-num` (including `@keyframes step-color` and `.step:hover .step-num`), `.step-title`, `.step-desc`.

- [ ] **Step 2: Add how-it-works HTML**

```html
<section id="how-it-works">
  <div class="section-inner">
    <div class="section-label">How it works</div>
    <div class="how-layout reveal">
      <div>
        <h2 class="how-headline">Your reputation<br/>opens doors.<br/><em>Agents walk<br/>through them.</em></h2>
        <p class="how-sub">We handle everything from attracting clients to delivering the work. Your only job is to be the expert you already are — and approve what comes back.</p>
      </div>
      <div class="steps">
        <div class="step">
          <span class="step-num">01</span>
          <div>
            <div class="step-title">We market your agency for you</div>
            <div class="step-desc">Our agents run your agency's marketing end-to-end — publishing content, building your presence, and pitching to prospects. Every campaign is built around your name, your résumé, and your track record. Clients don't hire a faceless firm. They hire you — the CMO who scaled a unicorn, the lawyer who won the landmark case. The agents make sure the right people know it.</div>
          </div>
        </div>
        <div class="step">
          <span class="step-num">02</span>
          <div>
            <div class="step-title">You meet the client — fully prepared</div>
            <div class="step-desc">When a prospect is ready to talk, agents prepare everything: a full client brief, their company background, the pain points to address, a tailored proposal, and talking points calibrated to your style. You walk in knowing exactly what to say. Your only job is to be in the room — and make them trust you.</div>
          </div>
        </div>
        <div class="step">
          <span class="step-num">03</span>
          <div>
            <div class="step-title">AI agents deliver the work</div>
            <div class="step-desc">A coordinated team of AI agents — guided by your professional standards — produces strategies, documents, analyses, and deliverables. Human specialists refine where nuance matters.</div>
          </div>
        </div>
        <div class="step">
          <span class="step-num">04</span>
          <div>
            <div class="step-title">You review, validate, and earn</div>
            <div class="step-desc">You apply your judgment to approve the work. Every hour you invest is multiplied by AI leverage — billed accordingly.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 3: Verify in browser**

Expect: 2-column layout, step numbers glow with colour on hover, section label shimmers.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: how it works section with 4 steps and colour-cycling step numbers"
```

---

## Task 11: The Model Section

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add billing figure CSS**

```css
.billing-figure {
  font-family: Georgia, serif;
  font-size: 32px;
  letter-spacing: -1px;
  background: linear-gradient(90deg, #fff 0%, #a78bfa 25%, #60a5fa 50%, #34d399 75%, #fff 100%);
  background-size: 300% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: billing-shimmer 3s linear infinite;
}
@keyframes billing-shimmer {
  0%   { background-position: 100% center; }
  100% { background-position: -100% center; }
}
```

- [ ] **Step 2: Add The Model section HTML**

Copy the full `<!-- THE CORE IDEA -->` section HTML from the mockup verbatim. This includes:
- The section wrapper with `id="the-model"`
- The 2-column copy + contrast boxes (top half)
- The full Marcus diagram panel (bottom half) with:
  - CMO avatar row + instruction bubble + time badge
  - 5 AI agent cards with inline SVG icons and status badges
  - 3 human specialist cards with Unsplash avatars
  - Output/billing bar at the bottom with `.billing-figure` class on `$24,000`
- Add `class="reveal"` to the top 2-column grid div and the diagram panel div

- [ ] **Step 3: Verify in browser**

Expect: The Model section visible on scroll, Marcus diagram renders, agent SVG icons visible, $24,000 has colour shimmer, agent cards have wild-border-sm on hover.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: the model section with Marcus diagram and billing shimmer"
```

---

## Task 12: Who It's For Section

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add who-its-for CSS**

Copy from mockup: `.profiles-grid`, `.profile-card`, `.profile-icon`, `.profile-title`, `.profile-desc`, `.profile-tags`, `.tag` (including all `nth-child` hover colour rules).

- [ ] **Step 2: Add who-its-for HTML**

```html
<section id="who">
  <div class="section-inner">
    <div class="section-label">Who it's for</div>
    <div class="profiles-grid reveal">

      <div class="profile-card wild-hover">
        <div class="profile-icon">⌘</div>
        <div class="profile-title">C-Suite Executives</div>
        <p class="profile-desc">You've led functions at scale. You know what good looks like, what failure looks like, and how to navigate the politics of both. That judgment is rare — and Aagency prices it that way.</p>
        <div class="profile-tags">
          <span class="tag">CMO</span>
          <span class="tag">CFO</span>
          <span class="tag">COO</span>
          <span class="tag">CTO</span>
          <span class="tag">CEO</span>
        </div>
      </div>

      <div class="profile-card wild-hover">
        <div class="profile-icon">◈</div>
        <div class="profile-title">Senior Domain Specialists</div>
        <p class="profile-desc">20+ years in law, engineering, design, finance, or medicine. You've built expertise that can't be replicated quickly. Aagency deploys that expertise at a scale no individual practice ever could.</p>
        <div class="profile-tags">
          <span class="tag">Lawyers</span>
          <span class="tag">Engineers</span>
          <span class="tag">Designers</span>
          <span class="tag">Advisors</span>
        </div>
      </div>

      <div class="profile-card" style="grid-column: span 2; background: var(--off-black);">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:60px; align-items:center;">
          <div>
            <div class="profile-title" style="font-size:28px; margin-bottom:16px;">You're the right fit if…</div>
            <ul style="list-style:none; display:flex; flex-direction:column; gap:14px;">
              <li style="font-size:13px; color:var(--text-secondary); display:flex; gap:12px;"><span style="color:var(--text-muted); flex-shrink:0;">—</span>You have 15+ years of senior professional experience</li>
              <li style="font-size:13px; color:var(--text-secondary); display:flex; gap:12px;"><span style="color:var(--text-muted); flex-shrink:0;">—</span>You want to earn on your own terms without managing a team</li>
              <li style="font-size:13px; color:var(--text-secondary); display:flex; gap:12px;"><span style="color:var(--text-muted); flex-shrink:0;">—</span>You're open to AI doing the heavy lifting while you lead</li>
              <li style="font-size:13px; color:var(--text-secondary); display:flex; gap:12px;"><span style="color:var(--text-muted); flex-shrink:0;">—</span>You value quality over volume</li>
            </ul>
          </div>
          <div>
            <div style="font-size:10px; letter-spacing:3px; text-transform:uppercase; color:var(--text-muted); margin-bottom:20px;">This is not for you if</div>
            <ul style="list-style:none; display:flex; flex-direction:column; gap:14px;">
              <li style="font-size:13px; color:var(--text-muted); display:flex; gap:12px;"><span style="flex-shrink:0;">—</span>You're early in your career and still building expertise</li>
              <li style="font-size:13px; color:var(--text-muted); display:flex; gap:12px;"><span style="flex-shrink:0;">—</span>You want to run a traditional consulting practice</li>
              <li style="font-size:13px; color:var(--text-muted); display:flex; gap:12px;"><span style="flex-shrink:0;">—</span>You're uncomfortable with AI-assisted delivery</li>
            </ul>
          </div>
        </div>
      </div>

    </div>
  </div>
</section>
```

- [ ] **Step 3: Verify in browser**

Expect: 2 profile cards with wild-border, tags light up in unique colours on hover, full-width fit/not-fit card below.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: who it's for section with coloured tags"
```

---

## Task 13: Booking & Footer Sections

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add booking CSS**

Copy from mockup: `.booking-layout`, `.booking-headline`, `.booking-desc`, `.booking-checklist`, `.booking-checklist li`, `.booking-checklist li::before` (including `@keyframes dash-color`), `.calendar-mock`, `.calendar-header`, `.calendar-slots`, `.slot`, `.slot:hover`, `.slot.selected`, `.slot-time`, `.slot-avail`, `.calendar-cta`.

- [ ] **Step 2: Add booking HTML**

```html
<section id="book">
  <div class="section-inner">
    <div class="section-label">Get started</div>
    <div class="booking-layout reveal">
      <div>
        <h2 class="booking-headline">15 minutes.<br/>That's all it takes<br/>to find out.</h2>
        <p class="booking-desc">Book a short discovery call. We'll tell you exactly what your agency could earn, which clients fit your background, and what the first 30 days look like.</p>
        <ul class="booking-checklist">
          <li>No pitch. No pressure. Just clarity.</li>
          <li>We'll assess fit honestly — not everyone qualifies.</li>
          <li>You'll leave with a realistic earnings projection.</li>
          <li>If it's right, onboarding takes less than a week.</li>
        </ul>
      </div>
      <div>
        <div class="calendar-mock">
          <div class="calendar-header">Book a discovery call · 15 min</div>
          <div class="calendar-slots">
            <div class="slot selected"><span class="slot-time">Mon, Mar 24 · 10:00 AM CET</span><span class="slot-avail">Available</span></div>
            <div class="slot"><span class="slot-time">Mon, Mar 24 · 2:00 PM CET</span><span class="slot-avail">Available</span></div>
            <div class="slot"><span class="slot-time">Tue, Mar 25 · 11:00 AM CET</span><span class="slot-avail">Available</span></div>
            <div class="slot"><span class="slot-time">Wed, Mar 26 · 9:30 AM CET</span><span class="slot-avail">Available</span></div>
          </div>
          <button class="calendar-cta wild-hover-sm" id="confirmBtn">Confirm this time →</button>
        </div>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 3: Add footer HTML**

```html
<footer id="footer">
  <div class="nav-logo" style="font-size:16px; opacity:0.5;">
    <span class="nav-logo-star" style="font-size:11px;">✦</span>
    <span style="font-family:Georgia,serif; font-style:italic; letter-spacing:-0.3px;">Aagency</span><span style="color:var(--text-muted); font-size:13px;">.ai</span>
  </div>
  <div class="footer-note">© 2026 · Invite only · All rights reserved</div>
</footer>
```

- [ ] **Step 4: Add footer CSS**

```css
footer {
  padding: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.footer-note {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 1px;
}
```

- [ ] **Step 5: Verify in browser**

Expect: booking section with rainbow-gradient slot borders on hover/select, animated checklist dashes, confirm button. Footer shows muted logo.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat: booking section and footer"
```

---

## Task 14: Booking Slot Interaction JS

**Files:**
- Modify: `index.html` (`<script>` block)

- [ ] **Step 1: Add slot picker + confirm JS**

```js
// ── SLOT PICKER ──
document.querySelectorAll('.slot').forEach(slot => {
  slot.addEventListener('click', () => {
    document.querySelectorAll('.slot').forEach(s => s.classList.remove('selected'));
    slot.classList.add('selected');
  });
});

// ── CONFIRM BUTTON ──
const confirmBtn = document.getElementById('confirmBtn');
confirmBtn.addEventListener('click', () => {
  confirmBtn.textContent = '✓ Confirmed — check your email';
  confirmBtn.style.background = '#1a1a1a';
  confirmBtn.style.color = '#888';
  confirmBtn.style.pointerEvents = 'none';
  confirmBtn.style.animation = 'none';
});
```

- [ ] **Step 2: Verify in browser**

Expect: clicking a slot selects it (rainbow gradient border), clicking another deselects previous. Confirm button grays out after click with success message.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: slot picker and confirm button interaction"
```

---

## Task 15: Final QA Pass

**Files:**
- Modify: `index.html` (fixes only)

- [ ] **Step 1: Full scroll-through check**

Open `index.html` in browser. Scroll from top to bottom. Verify:
- [ ] Nav is fixed, star animates, rainbow underlines work on hover
- [ ] Hero: headline lines animate in sequence, stats count up, photo mosaic parallaxes, cursor glow tracks and changes colour per cell, wild-border on hovered cells
- [ ] Section labels shimmer as you scroll past them
- [ ] Social proof: 3 cards, wild-border on hover, avatars visible
- [ ] How it works: step numbers glow on hover, 4 steps
- [ ] The Model: Marcus diagram visible, SVG agent icons, $24,000 shimmers, agent cards wild-border-sm on hover
- [ ] Who it's for: cards wild-border on hover, tags glow in unique colours
- [ ] Booking: slots have rainbow gradient on hover/select, checklist dashes animate, confirm works
- [ ] Footer: muted logo visible
- [ ] All `.reveal` blocks fade in on scroll entry (no sections stuck at opacity:0)

- [ ] **Step 2: Console errors check**

Open DevTools. Expect: zero errors.

- [ ] **Step 3: Fix any issues found**

- [ ] **Step 4: Final commit**

```bash
git add index.html
git commit -m "fix: QA pass — verify all sections, animations, and interactions"
```

---

## Quick Visual Reference

When implementing, keep the approved mockup open in another tab:

```
file:///home/bilelburaway/dev/Aagency/.superpowers/brainstorm/12156-1773886284/full-mockup.html
```

All CSS, SVG icons, Unsplash URLs, and HTML structure should be copied from the mockup. The plan tasks define what goes where and in what order — the mockup is the source of truth for exact values.
