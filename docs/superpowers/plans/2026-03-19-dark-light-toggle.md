# Dark/Light Mode Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a warm-white light mode and pill-switch toggle to the nav header in both `index.html` and `template.html`, persisted via `localStorage`.

**Architecture:** CSS custom properties are overridden under `[data-theme="light"]` on `<html>`. An inline anti-flash script in `<head>` reads `localStorage` before paint. A click handler on the toggle button flips the attribute and saves the preference. No new files are created — all changes are inline.

**Tech Stack:** Vanilla HTML, CSS custom properties, vanilla JavaScript, `localStorage`

---

## Files Modified

| File | What changes |
|------|-------------|
| `index.html` | CSS: light-mode vars, nav override, toggle styles, `.slot-confirmed`; HTML: anti-flash script, toggle button; JS: classList fix, toggle handler |
| `template.html` | Identical changes, plus `.powered-by` light override and `.method-step:hover` / `.client-card:hover` overrides (index.html has no matching elements) |

---

## Task 1: index.html — Add CSS

**Files:**
- Modify: `index.html` (insert before `</style>` at line 976)

- [ ] **Step 1: Add the CSS block**

Open `index.html`. Find `</style>` at line 976. Insert the following immediately before it:

```css
  /* ─── LIGHT MODE ─── */
  [data-theme="light"] {
    --black: #faf8f5;
    --off-black: #f2ede8;
    --border: #e8e3dc;
    --border-light: #d8d2c8;
    --text-primary: #1a1a1a;
    --text-secondary: #555;
    --text-muted: #999;
    --white: #1a1a1a;
  }
  [data-theme="light"] nav {
    background: rgba(250, 248, 245, 0.9);
  }
  [data-theme="light"] .powered-by {
    background: rgba(250, 248, 245, 0.9);
  }

  /* ─── THEME TOGGLE PILL ─── */
  .theme-toggle {
    position: relative;
    width: 48px;
    height: 26px;
    border-radius: 13px;
    border: 1px solid var(--border-light);
    background: var(--off-black);
    cursor: pointer;
    padding: 0;
    flex-shrink: 0;
    transition: background 0.3s, border-color 0.3s;
  }
  .theme-toggle::after {
    content: '☀️';
    position: absolute;
    right: 3px;
    top: 3px;
    width: 18px;
    height: 18px;
    line-height: 18px;
    text-align: center;
    font-size: 11px;
    border-radius: 50%;
    background: #f0f0f0;
    transition: right 0.3s;
  }
  [data-theme="light"] .theme-toggle::after {
    content: '🌙';
    right: auto;
    left: 3px;
    background: #333;
  }

  /* ─── CONFIRM BUTTON THEMED STATE ─── */
  .slot-confirmed {
    background: #1a1a1a !important;
    color: #888 !important;
    pointer-events: none;
    cursor: default;
  }
  [data-theme="light"] .slot-confirmed {
    background: #e8e3dc !important;
    color: #555 !important;
  }
```

- [ ] **Step 2: Verify**

Open `index.html` in a browser. Page should look unchanged (dark mode). No console errors.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(index): add light-mode CSS variables and toggle pill styles"
```

---

## Task 2: index.html — Add HTML (anti-flash script + toggle button)

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add anti-flash script to `<head>`**

In `index.html`, find the opening `<head>` tag (line 3). Insert the following as the very first child of `<head>` (before `<meta charset>`):

```html
<script>
  (function() {
    const t = localStorage.getItem('theme');
    if (t === 'light') document.documentElement.setAttribute('data-theme', 'light');
  })();
</script>
```

- [ ] **Step 2: Add toggle button to nav**

Find the `.nav-links` block (around line 988–992):

```html
  <div class="nav-links">
    <a href="#how-it-works">How it works</a>
    <a href="#who">Who it's for</a>
    <a href="#book" class="nav-cta">Book a call</a>
  </div>
```

Replace with:

```html
  <div class="nav-links">
    <a href="#how-it-works">How it works</a>
    <a href="#who">Who it's for</a>
    <button class="theme-toggle" id="themeToggle" aria-label="Toggle light/dark mode"></button>
    <a href="#book" class="nav-cta">Book a call</a>
  </div>
```

- [ ] **Step 3: Verify**

Reload `index.html`. The pill toggle should appear in the nav between "Who it's for" and "Book a call". Clicking it does nothing yet (JS not added). Check spacing looks balanced.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(index): add anti-flash script and theme toggle button to nav"
```

---

## Task 3: index.html — Fix JS (confirmBtn + theme handler)

**Files:**
- Modify: `index.html` (lines ~1577–1582 and end of `<script>`)

- [ ] **Step 1: Replace inline styles on confirmBtn**

Find this block (around lines 1577–1583):

```js
const confirmBtn = document.getElementById('confirmBtn');
confirmBtn.addEventListener('click', () => {
  confirmBtn.textContent = '✓ Confirmed — check your email';
  confirmBtn.style.background = '#1a1a1a';
  confirmBtn.style.color = '#888';
  confirmBtn.style.pointerEvents = 'none';
});
```

Replace with:

```js
const confirmBtn = document.getElementById('confirmBtn');
confirmBtn.addEventListener('click', () => {
  confirmBtn.textContent = '✓ Confirmed — check your email';
  confirmBtn.classList.add('slot-confirmed');
});
```

- [ ] **Step 2: Add theme toggle handler**

Find the closing `</script>` tag (line ~1584). Insert the following immediately before it:

```js
// Theme toggle
const themeToggle = document.getElementById('themeToggle');
const htmlEl = document.documentElement;
function applyTheme(theme) {
  htmlEl.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}
themeToggle.addEventListener('click', () => {
  applyTheme(htmlEl.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
});
```

- [ ] **Step 3: Verify**

Reload `index.html`. Click the toggle — page should switch to warm-white light mode. Click again — should return to dark. Reload the page in light mode — it should stay light (no flash). Click "Confirm this time →" in light mode — button should turn warm-beige, not dark.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(index): wire up theme toggle and fix confirmBtn to use CSS class"
```

---

## Task 4: template.html — Add CSS

**Files:**
- Modify: `template.html` (insert before `</style>` at line 678)

- [ ] **Step 1: Add the CSS block**

Open `template.html`. Find `</style>` at line 678. Insert the following immediately before it:

```css
  /* ─── LIGHT MODE ─── */
  [data-theme="light"] {
    --black: #faf8f5;
    --off-black: #f2ede8;
    --border: #e8e3dc;
    --border-light: #d8d2c8;
    --text-primary: #1a1a1a;
    --text-secondary: #555;
    --text-muted: #999;
    --white: #1a1a1a;
  }
  [data-theme="light"] nav {
    background: rgba(250, 248, 245, 0.9);
  }
  [data-theme="light"] .powered-by {
    background: rgba(250, 248, 245, 0.9);
  }
  [data-theme="light"] .method-step:hover { background: #ebe6df; }
  [data-theme="light"] .client-card:hover  { background: #ebe6df; }

  /* ─── THEME TOGGLE PILL ─── */
  .theme-toggle {
    position: relative;
    width: 48px;
    height: 26px;
    border-radius: 13px;
    border: 1px solid var(--border-light);
    background: var(--off-black);
    cursor: pointer;
    padding: 0;
    flex-shrink: 0;
    transition: background 0.3s, border-color 0.3s;
  }
  .theme-toggle::after {
    content: '☀️';
    position: absolute;
    right: 3px;
    top: 3px;
    width: 18px;
    height: 18px;
    line-height: 18px;
    text-align: center;
    font-size: 11px;
    border-radius: 50%;
    background: #f0f0f0;
    transition: right 0.3s;
  }
  [data-theme="light"] .theme-toggle::after {
    content: '🌙';
    right: auto;
    left: 3px;
    background: #333;
  }

  /* ─── CONFIRM BUTTON THEMED STATE ─── */
  .slot-confirmed {
    background: #1a1a1a !important;
    color: #888 !important;
    pointer-events: none;
    cursor: default;
  }
  [data-theme="light"] .slot-confirmed {
    background: #e8e3dc !important;
    color: #555 !important;
  }
```

- [ ] **Step 2: Verify**

Open `template.html` in a browser. Page should look unchanged (dark mode). No console errors.

- [ ] **Step 3: Commit**

```bash
git add template.html
git commit -m "feat(template): add light-mode CSS variables and toggle pill styles"
```

---

## Task 5: template.html — Add HTML (anti-flash script + toggle button)

**Files:**
- Modify: `template.html`

- [ ] **Step 1: Add anti-flash script to `<head>`**

In `template.html`, find the opening `<head>` tag. Insert the following as the very first child of `<head>` (before `<meta charset>`):

```html
<script>
  (function() {
    const t = localStorage.getItem('theme');
    if (t === 'light') document.documentElement.setAttribute('data-theme', 'light');
  })();
</script>
```

- [ ] **Step 2: Add toggle button to nav**

Find the `.nav-links` block (around lines 688–693):

```html
  <div class="nav-links">
    <a href="#about">About</a>
    <a href="#services">Services</a>
    <a href="#work">Work</a>
    <a href="#book" class="nav-cta">Book a call</a>
  </div>
```

Replace with:

```html
  <div class="nav-links">
    <a href="#about">About</a>
    <a href="#services">Services</a>
    <a href="#work">Work</a>
    <button class="theme-toggle" id="themeToggle" aria-label="Toggle light/dark mode"></button>
    <a href="#book" class="nav-cta">Book a call</a>
  </div>
```

- [ ] **Step 3: Verify**

Reload `template.html`. The pill toggle should appear in the nav. Spacing should look balanced.

- [ ] **Step 4: Commit**

```bash
git add template.html
git commit -m "feat(template): add anti-flash script and theme toggle button to nav"
```

---

## Task 6: template.html — Fix JS (confirmBtn + theme handler)

**Files:**
- Modify: `template.html` (lines ~1193–1198)

- [ ] **Step 1: Replace inline styles on confirmBtn**

Find this block (around lines 1193–1198):

```js
document.getElementById('confirmBtn').addEventListener('click', function() {
  this.textContent = '✓ Confirmed — check your email';
  this.style.background = '#1a1a1a';
  this.style.color = '#888';
  this.style.pointerEvents = 'none';
});
```

Replace with:

```js
document.getElementById('confirmBtn').addEventListener('click', function() {
  this.textContent = '✓ Confirmed — check your email';
  this.classList.add('slot-confirmed');
});
```

- [ ] **Step 2: Add theme toggle handler**

Find the closing `</script>` tag at the bottom of `template.html`. Insert the following immediately before it:

```js
// Theme toggle
const themeToggle = document.getElementById('themeToggle');
const htmlEl = document.documentElement;
function applyTheme(theme) {
  htmlEl.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}
themeToggle.addEventListener('click', () => {
  applyTheme(htmlEl.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
});
```

- [ ] **Step 3: Final verification checklist**

Open both files in a browser and verify:
- [ ] Toggle visible in header on both pages
- [ ] Clicking toggles between dark and warm-white
- [ ] Theme persists on reload (no flash)
- [ ] Toggle shows ☀️ in dark mode, 🌙 in light mode
- [ ] Knob is visible and contrasted in both modes
- [ ] Nav backdrop is warm-white in light mode
- [ ] `.powered-by` badge (template.html) is warm-white in light mode
- [ ] `.method-step:hover` and `.client-card:hover` use warm tones in light mode
- [ ] Confirm button is warm-beige in light mode after click

- [ ] **Step 4: Final commit**

```bash
git add template.html
git commit -m "feat(template): wire up theme toggle and fix confirmBtn to use CSS class"
```
