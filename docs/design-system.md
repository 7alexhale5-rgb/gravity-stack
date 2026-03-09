# Design System

The Gravity Stack design system is built for dark-mode technical documentation with a cinematic, high-contrast aesthetic. It uses three typefaces, a constrained color palette, and deliberate spacing to create a reading experience that feels more like a premium ebook than a typical docs site.

## Fonts

Three typefaces serve three distinct purposes:

| Font | Role | Source | Weight |
|------|------|--------|--------|
| **Instrument Serif** | Headings | Google Fonts (next/font/google) | 400 (Regular) |
| **Satoshi** | Body text | fontshare.com (next/font/local) | 400, 500, 700 |
| **DM Mono** | Code | Google Fonts (next/font/google) | 400 |

### Instrument Serif

An elegant serif face used exclusively for headings. Its high contrast and sharp serifs create visual authority against the dark background.

```css
font-family: var(--font-heading);
```

### Satoshi

A geometric sans-serif used for all body text, navigation, and UI elements. Self-hosted from fontshare.com (not available on Google Fonts). Load via `next/font/local` with the font files in `/public/fonts/`.

```css
font-family: var(--font-body);
```

### DM Mono

A monospace font for code blocks, inline code, terminal output, and technical labels.

```css
font-family: var(--font-mono);
```

### Font Loading

```typescript
// app/layout.tsx
import { Instrument_Serif, DM_Mono } from "next/font/google";
import localFont from "next/font/local";

const heading = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-heading",
});

const body = localFont({
  src: [
    { path: "../public/fonts/Satoshi-Regular.woff2", weight: "400" },
    { path: "../public/fonts/Satoshi-Medium.woff2", weight: "500" },
    { path: "../public/fonts/Satoshi-Bold.woff2", weight: "700" },
  ],
  variable: "--font-body",
});

const mono = DM_Mono({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-mono",
});
```

---

## Colors

The palette is minimal and purposeful. A near-black background with carefully chosen accent colors that each serve a specific semantic role.

### Background and Surface

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#040608` | Page background. Nearly black with a slight blue undertone. |
| `--s1` | `#0a0e12` | Surface level 1. Cards, panels. |
| `--s2` | `#111820` | Surface level 2. Elevated cards, modals. |
| `--s3` | `#1a2230` | Surface level 3. Hover states, active elements. |
| `--border` | `#1e293b` | Default border color. Subtle separation between elements. |

### Accent Colors

Each accent color has a specific semantic meaning. Do not use them interchangeably.

| Token | Hex | Meaning | Usage |
|-------|-----|---------|-------|
| `--electric` | `#00d4ff` | Primary / Interactive | Links, buttons, focus rings, primary actions |
| `--volt` | `#b8ff00` | Success / Active | Success states, active indicators, badges |
| `--heat` | `#ff4d2e` | Warning / Danger | Errors, destructive actions, critical alerts |
| `--nova` | `#c084fc` | Accent / Decorative | Tags, categories, secondary highlights |
| `--glow` | `#fbbf24` | Attention / Star | Ratings, featured items, important callouts |
| `--ice` | `#2dd4bf` | Info / Cool | Informational badges, secondary links, metadata |

### Text

| Token | Hex | Usage |
|-------|-----|-------|
| `--text` | `#e2e8f0` | Primary text. High contrast against dark backgrounds. |
| `--dim` | `#94a3b8` | Secondary text. Descriptions, timestamps, metadata. |
| `--muted` | `#64748b` | Tertiary text. Disabled states, placeholder text. |

### CSS Variables

Define these in your global CSS using Tailwind v4 `@theme`:

```css
@theme {
  --color-bg: #040608;
  --color-s1: #0a0e12;
  --color-s2: #111820;
  --color-s3: #1a2230;
  --color-border: #1e293b;
  --color-electric: #00d4ff;
  --color-volt: #b8ff00;
  --color-heat: #ff4d2e;
  --color-nova: #c084fc;
  --color-glow: #fbbf24;
  --color-ice: #2dd4bf;
  --color-text: #e2e8f0;
  --color-dim: #94a3b8;
  --color-muted: #64748b;
}
```

---

## Spacing

Consistent spacing creates rhythm and readability.

### Page Padding

| Token | Desktop | Mobile |
|-------|---------|--------|
| `--page-x` | `60px` | `24px` |
| `--page-y` | `48px` | `32px` |

### Component Spacing

| Context | Value |
|---------|-------|
| Section gap | `80px` |
| Card padding | `24px` |
| Card gap (grid) | `24px` |
| Inline spacing (icon to text) | `8px` |
| Stack spacing (label to input) | `6px` |

### CSS

```css
@theme {
  --spacing-page-x: 60px;
  --spacing-page-y: 48px;
  --spacing-page-x-mobile: 24px;
  --spacing-page-y-mobile: 32px;
  --spacing-section: 80px;
  --spacing-card: 24px;
  --spacing-card-gap: 24px;
}
```

---

## Radii

Rounded corners are used sparingly and consistently.

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-card` | `10px` | Cards, panels, modals |
| `--radius-button` | `8px` | Buttons, inputs |
| `--radius-badge` | `6px` | Badges, tags, chips |

```css
@theme {
  --radius-card: 10px;
  --radius-button: 8px;
  --radius-badge: 6px;
}
```

---

## Visual Effects

### Grain Overlay

A subtle film grain texture over the entire page. Creates depth and prevents the flat-screen look common in dark UIs.

```css
.grain::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 50;
  pointer-events: none;
  opacity: 0.03;
  background-image: url("/grain.svg");
  background-repeat: repeat;
}
```

### Gradient Text

Used for hero headings and emphasis text. Creates a luminous effect.

```css
.gradient-text {
  background: linear-gradient(135deg, var(--color-electric), var(--color-nova));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### Card Hover Glow

Cards emit a subtle glow on hover, drawing attention without being distracting.

```css
.card {
  background: var(--color-s1);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.card:hover {
  border-color: color-mix(in srgb, var(--color-electric) 30%, transparent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--color-electric) 8%, transparent);
}
```

### Sticky Nav Blur

The navigation bar uses a frosted glass effect when scrolling.

```css
.nav {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(12px);
  background: color-mix(in srgb, var(--color-bg) 80%, transparent);
  border-bottom: 1px solid var(--color-border);
}
```

---

## Layout

### Max Width

Content is constrained to `1400px` and centered on the page.

```css
.container {
  max-width: 1400px;
  margin-inline: auto;
  padding-inline: var(--spacing-page-x);
}

@media (max-width: 768px) {
  .container {
    padding-inline: var(--spacing-page-x-mobile);
  }
}
```

### Responsive Grid

Cards and content blocks use a responsive grid that adapts from 1 to 3 columns:

```css
.grid {
  display: grid;
  gap: var(--spacing-card-gap);
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

With Tailwind:

```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
  <!-- cards -->
</div>
```

---

## Quick Reference

```
Fonts:      Instrument Serif / Satoshi / DM Mono
Background: #040608
Surfaces:   #0a0e12 → #111820 → #1a2230
Border:     #1e293b
Accents:    electric #00d4ff | volt #b8ff00 | heat #ff4d2e
            nova #c084fc | glow #fbbf24 | ice #2dd4bf
Text:       #e2e8f0 / #94a3b8 / #64748b
Max Width:  1400px
Grid:       1 → 2 → 3 columns
Radii:      10px / 8px / 6px
```
