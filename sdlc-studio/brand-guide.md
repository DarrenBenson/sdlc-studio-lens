# SDLC Studio Lens: Brand Identity & Design System

**Version:** 1.0.0
**Status:** Draft
**Date:** February 2026

---

## 1. Core Philosophy

**Your SDLC artefacts, at a glance.**

SDLC Studio Lens draws from modern finance dashboards - data-dense, calm, professional. Dark surfaces recede; bright lime green highlights what matters. Every pixel serves comprehension, not decoration.

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Data-Dense** | Pack information tightly. Cards, badges, and metrics over whitespace. |
| **Calm Dark** | Dark mode that feels premium, not oppressive. Subtle green warmth in backgrounds. |
| **Status at a Glance** | Colour tells the story before text does. Green = done, blue = progress, red = blocked. |
| **Read-Only Clarity** | The dashboard displays, never edits. UI should feel like a control panel, not a form builder. |

### Keywords

- Dashboard, Overview, Lens, Insight, Status
- Documents, Artefacts, Epics, Stories, Progress
- Sync, Parse, Browse, Search, Filter

### Anti-Patterns

- No flat grey corporate dashboards
- No harsh pure black backgrounds (#000000)
- No light mode (dark only, by design)
- No excessive gradients or glassmorphism
- No decorative illustrations or mascots
- No rounded-everything (cards round, badges tighter)

---

## 2. Logo & Wordmark

### Wordmark

**Full:** `SDLC Studio Lens`
**Display:** `Studio Lens`
**Short:** `Lens`

**Typography:** Space Grotesk Bold
**Colour:** Lime Green (#A3E635) on dark backgrounds

### Logo Concept

A minimal lens/eye icon combined with a document stack, representing focused insight into SDLC documents.

```
  ┌─────────────────┐
  │    ╭──────╮      │
  │   ( ◉ Lens )     │
  │    ╰──────╯      │
  │   ═══════════    │
  │   ═══════════    │
  │   ═══════        │
  └─────────────────┘
```

### Logo Specifications

| Context | Format | Minimum Size |
|---------|--------|--------------|
| Favicon | Icon only | 16x16px |
| Sidebar header | Icon + "Studio Lens" | 32px height |
| Splash/loading | Icon + full name | 48px height |

---

## 3. Colour System

### The "Lens" Palette

Inspired by modern finance dashboards - green-tinted dark surfaces with bright lime accents. The background has subtle green warmth rather than the cold blue of GitHub-style darks.

#### Background Colours

| Role | Name | Hex | RGB | Usage |
|------|------|-----|-----|-------|
| **Background Base** | Deep Forest | `#0B0F0D` | 11, 15, 13 | Page background |
| **Background Surface** | Dark Canopy | `#111916` | 17, 25, 22 | Cards, panels, sidebar |
| **Background Elevated** | Moss Dark | `#1C2520` | 28, 37, 32 | Hover states, active surfaces, inputs |
| **Background Overlay** | Shadow Green | `#243029` | 36, 48, 41 | Dropdowns, modals, overlays |

#### Border Colours

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| **Border Default** | Grid Line | `#2A3631` | Card borders, dividers |
| **Border Subtle** | Faint Edge | `#1E2B24` | Subtle separators |
| **Border Strong** | Clear Edge | `#3D4F46` | Focused inputs, hover cards |

#### Text Colours

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| **Text Primary** | Bright White | `#F0F6F0` | Headlines, important content |
| **Text Secondary** | Soft Grey | `#B0BEC5` | Body text, descriptions |
| **Text Tertiary** | Dim Grey | `#78909C` | Labels, captions, timestamps |
| **Text Muted** | Faded | `#4A5B53` | Disabled, placeholder text |

#### Accent Colours

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| **Accent Primary** | Lime Green | `#A3E635` | Primary actions, active states, highlights |
| **Accent Hover** | Lime Bright | `#BEF264` | Hover states |
| **Accent Pressed** | Lime Deep | `#84CC16` | Pressed/active states |
| **Accent Muted** | Lime Glow | `rgba(163, 230, 53, 0.15)` | Glow effects, chart fills, subtle highlights |

#### Status Colours

| Status | Name | Hex | Glow Hex | Usage |
|--------|------|-----|----------|-------|
| **Done/Success** | Complete Green | `#A3E635` | `rgba(163, 230, 53, 0.2)` | Done, synced, healthy |
| **In Progress** | Active Blue | `#3B82F6` | `rgba(59, 130, 246, 0.2)` | In Progress, syncing |
| **Draft** | Neutral Grey | `#78909C` | `rgba(120, 144, 156, 0.2)` | Draft, Not Started |
| **Blocked/Error** | Alert Red | `#EF4444` | `rgba(239, 68, 68, 0.2)` | Blocked, error, failed |
| **Warning** | Caution Amber | `#F59E0B` | `rgba(245, 158, 11, 0.2)` | Warnings, review needed |

#### Chart Palette

| Name | Hex | Usage |
|------|-----|-------|
| Chart Green | `#A3E635` | Primary data series, completion |
| Chart Blue | `#3B82F6` | Secondary data series, in progress |
| Chart Amber | `#F59E0B` | Tertiary data series, warnings |
| Chart Red | `#EF4444` | Quaternary data series, blocked |
| Chart Purple | `#A78BFA` | Quinary data series, other |
| Chart Cyan | `#22D3EE` | Senary data series, accent |

### Colour Application Rules

1. **Status always wins:** If something has a status, its colour comes from the Status palette
2. **Lime green is the accent:** Use sparingly for emphasis - active states, primary buttons, progress fills
3. **Glow for depth:** Use muted accent as background glow behind charts and active elements
4. **Text on dark:** Ensure WCAG AA contrast (4.5:1 minimum) for all text
5. **One bright colour per component:** Do not mix multiple bright colours in the same card

### Semantic Tokens (CSS Custom Properties)

```css
:root {
  /* Backgrounds */
  --bg-base: #0B0F0D;
  --bg-surface: #111916;
  --bg-elevated: #1C2520;
  --bg-overlay: #243029;

  /* Borders */
  --border-default: #2A3631;
  --border-subtle: #1E2B24;
  --border-strong: #3D4F46;

  /* Text */
  --text-primary: #F0F6F0;
  --text-secondary: #B0BEC5;
  --text-tertiary: #78909C;
  --text-muted: #4A5B53;

  /* Accent */
  --accent-primary: #A3E635;
  --accent-hover: #BEF264;
  --accent-pressed: #84CC16;
  --accent-muted: rgba(163, 230, 53, 0.15);

  /* Status */
  --status-done: #A3E635;
  --status-done-glow: rgba(163, 230, 53, 0.2);
  --status-progress: #3B82F6;
  --status-progress-glow: rgba(59, 130, 246, 0.2);
  --status-draft: #78909C;
  --status-draft-glow: rgba(120, 144, 156, 0.2);
  --status-blocked: #EF4444;
  --status-blocked-glow: rgba(239, 68, 68, 0.2);
  --status-warning: #F59E0B;
  --status-warning-glow: rgba(245, 158, 11, 0.2);
}
```

---

## 4. Typography System

### Font Stack

#### Primary: Space Grotesk

**Usage:** Headlines, titles, navigation, buttons
**Character:** Geometric, modern, excellent legibility at all sizes
**Weights:** Medium (500), SemiBold (600), Bold (700)
**Source:** Google Fonts (free)

```css
font-family: 'Space Grotesk', system-ui, sans-serif;
```

#### Secondary: JetBrains Mono

**Usage:** Data, metrics, document IDs, code blocks, timestamps, metadata values
**Character:** Purpose-built for code, excellent number legibility
**Weights:** Regular (400), Medium (500), Bold (700)
**Source:** Google Fonts (free)

```css
font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

#### Body: Inter

**Usage:** Body text, descriptions, document content, paragraphs
**Character:** Clean, neutral, optimised for screen reading
**Weights:** Regular (400), Medium (500)
**Source:** Google Fonts (free)

```css
font-family: 'Inter', system-ui, sans-serif;
```

### Type Scale

| Name | Size | Line Height | Weight | Font | Usage |
|------|------|-------------|--------|------|-------|
| **Display** | 36px / 2.25rem | 1.1 | 700 | Space Grotesk | Hero metrics (total documents) |
| **H1** | 28px / 1.75rem | 1.2 | 700 | Space Grotesk | Page titles |
| **H2** | 22px / 1.375rem | 1.3 | 600 | Space Grotesk | Section headers |
| **H3** | 18px / 1.125rem | 1.4 | 600 | Space Grotesk | Card titles |
| **H4** | 15px / 0.9375rem | 1.4 | 500 | Space Grotesk | Subsections |
| **Body** | 14px / 0.875rem | 1.6 | 400 | Inter | Body copy, document content |
| **Body Small** | 12px / 0.75rem | 1.5 | 400 | Inter | Secondary text |
| **Data Large** | 28px / 1.75rem | 1.1 | 700 | JetBrains Mono | Big stat numbers |
| **Data Medium** | 18px / 1.125rem | 1.2 | 500 | JetBrains Mono | Metric values |
| **Data Small** | 13px / 0.8125rem | 1.4 | 400 | JetBrains Mono | Timestamps, doc IDs |
| **Label** | 11px / 0.6875rem | 1.3 | 500 | JetBrains Mono | Uppercase labels |
| **Code** | 13px / 0.8125rem | 1.5 | 400 | JetBrains Mono | Code blocks in documents |

### Typography CSS

```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500&display=swap');

body {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

h1, h2, h3, h4 {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  color: var(--text-primary);
  margin: 0;
}

code, .metric, .timestamp, .doc-id, [data-mono] {
  font-family: 'JetBrains Mono', monospace;
}

.label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
}
```

---

## 5. Spacing System

### Base Unit

**4px base** - All spacing derived from multiples of 4px.

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight gaps, icon padding |
| `--space-2` | 8px | Related element gaps |
| `--space-3` | 12px | Default padding |
| `--space-4` | 16px | Card padding, section gaps |
| `--space-5` | 20px | Component margins |
| `--space-6` | 24px | Large gaps |
| `--space-8` | 32px | Section margins |
| `--space-10` | 40px | Page section spacing |

---

## 6. Border Radius System

Generous rounding - modern and approachable, matching the reference dashboard aesthetic.

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Badges, tags, small chips |
| `--radius-md` | 10px | Buttons, inputs |
| `--radius-lg` | 14px | Cards, panels |
| `--radius-xl` | 18px | Large cards, sidebar active pill |
| `--radius-full` | 9999px | Circular indicators, progress rings |

---

## 7. Shadow & Glow System

Shadows are minimal on dark backgrounds. Glow effects add depth where green accent is present.

```css
:root {
  /* Elevation shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.5);

  /* Accent glow (for charts, active elements) */
  --glow-accent: 0 0 40px rgba(163, 230, 53, 0.08);
  --glow-accent-strong: 0 0 60px rgba(163, 230, 53, 0.15);

  /* Status glows */
  --glow-done: 0 0 12px var(--status-done-glow);
  --glow-progress: 0 0 12px var(--status-progress-glow);
  --glow-blocked: 0 0 12px var(--status-blocked-glow);
}
```

---

## 8. Component Library

### 8.1 Status Badge

The signature element - a coloured pill that shows document status at a glance.

```css
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.status-badge--done {
  background-color: rgba(163, 230, 53, 0.15);
  color: #A3E635;
}

.status-badge--in-progress {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3B82F6;
}

.status-badge--draft {
  background-color: rgba(120, 144, 156, 0.15);
  color: #78909C;
}

.status-badge--blocked {
  background-color: rgba(239, 68, 68, 0.15);
  color: #EF4444;
}

.status-badge--not-started {
  background-color: rgba(74, 90, 82, 0.15);
  color: #4A5B53;
}

/* Dot indicator before text */
.status-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background-color: currentColor;
}
```

### 8.2 Type Badge

Identifies document type (epic, story, bug, plan, etc.)

```css
.type-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background-color: var(--bg-elevated);
  color: var(--text-tertiary);
  border: 1px solid var(--border-subtle);
}

.type-badge--epic    { color: #A78BFA; border-color: rgba(167, 139, 250, 0.3); }
.type-badge--story   { color: #3B82F6; border-color: rgba(59, 130, 246, 0.3); }
.type-badge--bug     { color: #EF4444; border-color: rgba(239, 68, 68, 0.3); }
.type-badge--plan    { color: #F59E0B; border-color: rgba(245, 158, 11, 0.3); }
.type-badge--prd     { color: #A3E635; border-color: rgba(163, 230, 53, 0.3); }
.type-badge--trd     { color: #22D3EE; border-color: rgba(34, 211, 238, 0.3); }
.type-badge--tsd     { color: #F472B6; border-color: rgba(244, 114, 182, 0.3); }
```

### 8.3 Project Card

Dashboard landing page element showing project health at a glance.

```css
.project-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  cursor: pointer;
}

.project-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--glow-accent);
}

.project-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-4);
}

.project-card__name {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.project-card__sync-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-tertiary);
}

.project-card__stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.project-card__stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.project-card__stat-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.project-card__progress {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
}

.project-card__percentage {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  color: var(--accent-primary);
}
```

### 8.4 Document Card

List item for document browsing.

```css
.document-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background-color: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: background-color 0.15s ease, border-color 0.15s ease;
  cursor: pointer;
}

.document-card:hover {
  background-color: var(--bg-elevated);
  border-color: var(--border-default);
}

.document-card__title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
}

.document-card__id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-tertiary);
  min-width: 60px;
}

.document-card__meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-tertiary);
}
```

### 8.5 Stats Card

Compact metric display with large number.

```css
.stats-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  text-align: center;
}

.stats-card__value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: var(--space-1);
}

.stats-card__label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
}

.stats-card__change {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 500;
  margin-top: var(--space-2);
}

.stats-card__change--positive { color: var(--accent-primary); }
.stats-card__change--negative { color: var(--status-blocked); }
```

### 8.6 Progress Ring

SVG-based circular progress indicator for completion percentage.

```css
.progress-ring {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.progress-ring__circle-bg {
  fill: none;
  stroke: var(--bg-elevated);
  stroke-width: 4;
}

.progress-ring__circle-fill {
  fill: none;
  stroke: var(--accent-primary);
  stroke-width: 4;
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dashoffset 0.6s ease;
}

.progress-ring__value {
  position: absolute;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--text-primary);
}
```

### 8.7 Buttons

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}

/* Primary - Lime Green */
.btn--primary {
  background-color: var(--accent-primary);
  color: var(--bg-base);
  border-color: var(--accent-primary);
}

.btn--primary:hover {
  background-color: var(--accent-hover);
  border-color: var(--accent-hover);
}

/* Secondary - Ghost */
.btn--secondary {
  background-color: transparent;
  color: var(--text-secondary);
  border-color: var(--border-default);
}

.btn--secondary:hover {
  background-color: var(--bg-elevated);
  color: var(--text-primary);
  border-color: var(--border-strong);
}

/* Danger - Red outline */
.btn--danger {
  background-color: transparent;
  color: var(--status-blocked);
  border-color: var(--status-blocked);
}

.btn--danger:hover {
  background-color: var(--status-blocked);
  color: var(--bg-base);
}

/* Sync button (accent outline with icon) */
.btn--sync {
  background-color: var(--accent-muted);
  color: var(--accent-primary);
  border-color: rgba(163, 230, 53, 0.3);
}

.btn--sync:hover {
  background-color: rgba(163, 230, 53, 0.25);
  border-color: var(--accent-primary);
}
```

### 8.8 Input Fields

```css
.input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.input::placeholder {
  color: var(--text-muted);
}

.input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-muted);
}
```

### 8.9 Sidebar Navigation

```css
.sidebar {
  width: 240px;
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-default);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  margin-bottom: var(--space-4);
}

.sidebar__logo-text {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: var(--accent-primary);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background-color: var(--bg-elevated);
  color: var(--text-primary);
}

/* Active state: filled lime green pill (matches reference design) */
.nav-item--active {
  background-color: var(--accent-primary);
  color: var(--bg-base);
}

.nav-item--active .nav-item__icon {
  color: var(--bg-base);
}
```

### 8.10 Search Bar

Global search input in the header area.

```css
.search-bar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  min-width: 280px;
  transition: border-color 0.15s ease;
}

.search-bar:focus-within {
  border-color: var(--accent-primary);
}

.search-bar__icon {
  color: var(--text-tertiary);
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.search-bar__input {
  background: none;
  border: none;
  outline: none;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  width: 100%;
}

.search-bar__input::placeholder {
  color: var(--text-muted);
}
```

---

## 9. Iconography

### Icon Library

Use **Lucide Icons** (https://lucide.dev) - open source, consistent, works well at small sizes.

### Key Icons

| Concept | Icon Name | Usage |
|---------|-----------|-------|
| Dashboard | `layout-dashboard` | Navigation |
| Documents | `file-text` | Document list |
| Search | `search` | Search bar, search page |
| Settings | `settings` | Project management |
| Sync | `refresh-cw` | Sync trigger button |
| Syncing | `loader-2` (animated) | Sync in progress |
| Projects | `folder-open` | Project list |
| Filter | `filter` | Filter controls |
| Sort | `arrow-up-down` | Sort controls |
| Epic | `layers` | Epic document type |
| Story | `bookmark` | Story document type |
| Bug | `bug` | Bug document type |
| Plan | `map` | Plan document type |
| Test | `flask-conical` | Test spec type |
| PRD/TRD/TSD | `file-text` | Specification types |
| Chevron | `chevron-right` | Navigation, breadcrumbs |
| External | `external-link` | Links to filesystem paths |
| Copy | `copy` | Copy document ID |

### Icon Sizing

| Context | Size | Stroke Width |
|---------|------|--------------|
| Navigation | 18px | 2px |
| Card inline | 16px | 2px |
| Button with text | 16px | 2px |
| Type badge | 14px | 2px |
| Large display | 24px | 1.5px |

### Icon Colours

- Default: `var(--text-tertiary)` (#78909C)
- Interactive hover: `var(--text-primary)` (#F0F6F0)
- Active nav: `var(--bg-base)` (dark, on lime green background)
- Status icons: Use matching status colour

---

## 10. Chart Styling

### Chart Backgrounds

Charts sit on card backgrounds with a subtle accent glow behind the data area:

```css
.chart-container {
  position: relative;
  background-color: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

/* Subtle green glow behind chart area */
.chart-container::before {
  content: '';
  position: absolute;
  top: 30%;
  left: 20%;
  width: 60%;
  height: 40%;
  background: radial-gradient(
    ellipse at center,
    rgba(163, 230, 53, 0.06) 0%,
    transparent 70%
  );
  pointer-events: none;
}
```

### Recharts Customisation

```typescript
const chartTheme = {
  // Axis styling
  axisStroke: '#2A3631',
  axisTickColor: '#78909C',
  axisFontFamily: "'JetBrains Mono', monospace",
  axisFontSize: 11,

  // Grid
  gridStroke: '#1E2B24',
  gridStrokeDasharray: '3 3',

  // Tooltip
  tooltipBg: '#1C2520',
  tooltipBorder: '#2A3631',
  tooltipFontFamily: "'JetBrains Mono', monospace",

  // Area fill gradient
  areaFillStart: 'rgba(163, 230, 53, 0.3)',
  areaFillEnd: 'rgba(163, 230, 53, 0.02)',
  lineStroke: '#A3E635',
  lineStrokeWidth: 2,
};
```

### Donut/Pie Charts

Status breakdown uses the status colour palette:

| Segment | Colour |
|---------|--------|
| Done | `#A3E635` |
| In Progress | `#3B82F6` |
| Draft | `#78909C` |
| Blocked | `#EF4444` |
| Not Started | `#4A5B53` |

---

## 11. Animation & Motion

### Principles

1. **Subtle over flashy** - animations support understanding, not distract
2. **Fast by default** - most transitions 150ms
3. **Purposeful** - sync spinner and progress ring are the primary motion elements
4. **Reduced motion respected** - honour `prefers-reduced-motion`

### Timing

```css
:root {
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --duration-fast: 100ms;
  --duration-normal: 150ms;
  --duration-slow: 300ms;
}
```

### Sync Spinner

```css
.sync-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 12. Layout Patterns

### Application Shell

```css
.app {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  background-color: var(--bg-base);
}

.app__sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.app__main {
  padding: var(--space-6);
  overflow-y: auto;
}

.app__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
}
```

### Dashboard Grid

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-4);
}
```

### Document List

```css
.document-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
```

### Document View

```css
.document-view {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: var(--space-6);
}

.document-view__content {
  /* Rendered markdown */
  max-width: 800px;
}

.document-view__sidebar {
  /* Frontmatter metadata */
  position: sticky;
  top: var(--space-6);
  align-self: start;
}
```

---

## 13. Tailwind CSS Configuration

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        'bg-base': '#0B0F0D',
        'bg-surface': '#111916',
        'bg-elevated': '#1C2520',
        'bg-overlay': '#243029',

        // Borders
        'border-default': '#2A3631',
        'border-subtle': '#1E2B24',
        'border-strong': '#3D4F46',

        // Text
        'text-primary': '#F0F6F0',
        'text-secondary': '#B0BEC5',
        'text-tertiary': '#78909C',
        'text-muted': '#4A5B53',

        // Accent
        'accent': {
          DEFAULT: '#A3E635',
          hover: '#BEF264',
          pressed: '#84CC16',
          muted: 'rgba(163, 230, 53, 0.15)',
        },

        // Status
        'status-done': '#A3E635',
        'status-progress': '#3B82F6',
        'status-draft': '#78909C',
        'status-blocked': '#EF4444',
        'status-warning': '#F59E0B',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        md: '10px',
        lg: '14px',
        xl: '18px',
      },
    },
  },
  plugins: [],
} satisfies Config;
```

---

## 14. Markdown Rendering Theme

Document view renders sdlc-studio markdown with these overrides:

```css
.markdown-body {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  font-family: 'Space Grotesk', sans-serif;
  color: var(--text-primary);
  margin-top: var(--space-8);
  margin-bottom: var(--space-3);
}

.markdown-body code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  background-color: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--accent-primary);
}

.markdown-body pre {
  background-color: var(--bg-base);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  overflow-x: auto;
}

.markdown-body pre code {
  background: none;
  padding: 0;
  color: var(--text-secondary);
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
}

.markdown-body th {
  background-color: var(--bg-elevated);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-default);
  text-align: left;
}

.markdown-body td {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
}

.markdown-body blockquote {
  border-left: 3px solid var(--accent-primary);
  margin: var(--space-4) 0;
  padding: var(--space-2) var(--space-4);
  background-color: var(--accent-muted);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.markdown-body a {
  color: var(--accent-primary);
  text-decoration: none;
}

.markdown-body a:hover {
  color: var(--accent-hover);
  text-decoration: underline;
}
```

---

## 15. Assets Checklist

| Asset | Format | Sizes |
|-------|--------|-------|
| Favicon | .ico, .png | 16, 32, 48 |
| App icon | .png | 180, 192, 512 |
| OG image | .png | 1200x630 |
| Logo (icon) | .svg | Vector |
| Logo (full wordmark) | .svg | Vector |

---

## 16. Colour Supersedes

This brand guide supersedes colour references in other documents:

| Document | Old Value | New Value |
|----------|-----------|-----------|
| PRD §1 bg-base | `#0D1117` | `#0B0F0D` |
| PRD §1 bg-card | `#161B22` | `#111916` |
| PRD §1 bg-elevated | `#21262D` | `#1C2520` |
| PRD §1 accent-primary | `#10B981` (emerald) | `#A3E635` (lime) |
| PRD §1 accent-hover | `#059669` | `#BEF264` |
| TRD §14 all colour tokens | See old table | See §3 of this guide |

> **This document is the authoritative source for all visual design decisions.** PRD and TRD colour values are now for reference only - the brand guide takes precedence.

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-17 | 1.0.0 | Initial brand guide created from reference design |
