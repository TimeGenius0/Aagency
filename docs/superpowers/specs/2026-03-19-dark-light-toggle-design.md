# Dark/Light Mode Toggle — Design Spec

**Date:** 2026-03-19
**Status:** Approved (post-review)
**Files affected:** `index.html`, `template.html`

---

## Overview

Add a pill-switch toggle to the fixed navigation header in both `index.html` and `template.html`, allowing users to switch between the existing dark theme and a new warm-white light theme. The preference is persisted in `localStorage`.

---

## Toggle Component

- **Style:** Pill switch (48×26px, border-radius 13px)
- **Placement:** Inside `.nav-links`, between the last nav link and the `.nav-cta` button
- **Dark state:** Dark pill background, knob on the right showing ☀️
- **Light state:** Light pill background, knob on the left showing 🌙
- **Element:** `<button class="theme-toggle" id="themeToggle" aria-label="Toggle light/dark mode">`

Note: `index.html` has `<nav>` with no `id`. `template.html` has `<nav id="nav">`. All CSS overrides must use the `nav` tag selector (not `#nav`) to work in both files.

The `.nav-links` flex container uses `gap: 36px`. The toggle (48×26px) will sit inside that gap naturally. No gap adjustment is needed, but verify visually after implementation that spacing around the toggle feels balanced — add a small negative margin if needed.

---

## Theming Implementation

**Approach:** CSS custom properties + `data-theme` attribute on `<html>`

### Default (dark — no attribute)

Existing `:root` variables remain unchanged:

```css
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
```

### Light mode (`[data-theme="light"]`)

```css
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
```

### Hardcoded color overrides (not covered by variables)

Both files use `rgba(8,8,8,0.92)` for the nav backdrop — not a CSS variable. Override it explicitly:

```css
[data-theme="light"] nav {
  background: rgba(250, 248, 245, 0.9);
}
```

`template.html` additionally has a `.powered-by` fixed badge with `background: rgba(8,8,8,0.9)`. Override it:

```css
[data-theme="light"] .powered-by {
  background: rgba(250, 248, 245, 0.9);
}
```
*(This rule has no effect in `index.html` which has no `.powered-by` element — safe to include in both.)*

Both files also use the hardcoded literal `#111` for hover states (not a CSS variable):

```css
[data-theme="light"] .method-step:hover { background: #ebe6df; }
[data-theme="light"] .client-card:hover  { background: #ebe6df; }
```

---

## CSS — Toggle Pill Styles

```css
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
```

Notes:
- `transition: content` is not valid CSS and is omitted.
- The knob background changes from `#f0f0f0` (readable on dark pill) to `#333` (readable on cream pill) in light mode.

---

## JavaScript

### 1. Anti-flash inline script (in `<head>`, before stylesheets)

```html
<script>
  (function() {
    const t = localStorage.getItem('theme');
    if (t === 'light') document.documentElement.setAttribute('data-theme', 'light');
  })();
</script>
```

### 2. Toggle handler (at bottom of `<body>`, alongside existing JS)

```js
const toggle = document.getElementById('themeToggle');
const html = document.documentElement;
function applyTheme(theme) {
  html.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}
toggle.addEventListener('click', () => {
  applyTheme(html.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
});
```

### 3. Booking confirm button — inline style fix

Both files set dark colors via `element.style` on the confirm button, which overrides any CSS theme rule:

- `index.html`: `confirmBtn.style.background = '#1a1a1a'; confirmBtn.style.color = '#888';`
- `template.html`: `this.style.background = '#1a1a1a'; this.style.color = '#888';`

**Fix:** Replace all three inline style assignments (`background`, `color`, `pointerEvents`) with a CSS class `.slot-confirmed`. Remove all `element.style.*` lines and add the class via `element.classList.add('slot-confirmed')` instead. Add light-mode styles for the class:

```css
.slot-confirmed {
  background: #1a1a1a;
  color: #888;
  pointer-events: none;
  cursor: default;
}
[data-theme="light"] .slot-confirmed {
  background: #e8e3dc;
  color: #555;
}
```

---

## Scope & Constraints

- Dark mode is the default (no `data-theme` attribute = dark)
- Both `index.html` and `template.html` receive identical changes unless noted otherwise
- No new files created — all changes are inline within each HTML file
- Existing accent colors and shimmer animations are unchanged in both modes (shimmer endpoints use `#fff` which remains visually acceptable on the warm-white background)
- The cursor glow (`rgba(255,255,255,0.04)`) naturally becomes invisible in light mode — this is acceptable

---

## Success Criteria

- [ ] Toggle is visible in the header on both pages
- [ ] Clicking the toggle switches between dark and warm-white themes
- [ ] Theme persists on page reload via `localStorage`
- [ ] No flash of wrong theme on load
- [ ] All text remains readable in both modes
- [ ] Toggle pill icon updates correctly (☀️ in dark, 🌙 in light)
- [ ] Knob contrast is legible in both modes
- [ ] Nav backdrop is warm-white in light mode (not dark)
- [ ] `.powered-by` badge (template.html) is warm-white in light mode
- [ ] Hover states on `.method-step` and `.client-card` use warm tones in light mode
- [ ] Booking confirm button uses appropriate colors in both modes
