# Dark/Light Mode Toggle — Design Spec

**Date:** 2026-03-19
**Status:** Approved
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

### Nav background override

The nav backdrop is hardcoded in `#nav` CSS (not a variable), so it needs an explicit override:

```css
[data-theme="light"] #nav {
  background: rgba(250, 248, 245, 0.9);
}
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
  transition: right 0.3s, content 0.3s;
}
[data-theme="light"] .theme-toggle::after {
  content: '🌙';
  right: auto;
  left: 3px;
}
```

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

---

## Scope & Constraints

- Dark mode is the default (no `data-theme` attribute = dark)
- Both `index.html` and `template.html` receive identical changes
- No new files created — all changes are inline within each HTML file
- Existing accent colors and animations are unchanged in both modes
- The nav backdrop blur background is the only hardcoded color that needs an explicit light override — all other colors flow through CSS variables

---

## Success Criteria

- [ ] Toggle is visible in the header on both pages
- [ ] Clicking the toggle switches between dark and warm-white themes
- [ ] Theme persists on page reload via `localStorage`
- [ ] No flash of wrong theme on load
- [ ] All text remains readable in both modes
- [ ] Toggle pill icon updates correctly (☀️ in dark, 🌙 in light)
