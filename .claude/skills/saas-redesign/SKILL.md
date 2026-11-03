---
name: saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a vertical navigation sidebar on the left (replacing the top nav bar), a consistent spacing/type/color token system, and a polished professional look. Use this skill whenever the user asks to modernize, restyle, redesign, polish or "make more professional" a Vue app's interface, wants a sidebar or left/side navigation instead of a top navbar, asks for an app shell, dashboard layout, SaaS look and feel, design tokens, consistent spacing, collapsible sidebar, or dark mode for a Vue 3 project, even if they never say "SaaS" or "skill".
---

# SaaS-style redesign for Vue 3 apps

Turn an existing Vue 3 app into a modern SaaS interface: a left sidebar for navigation, a slim top bar for utilities, a content area with consistent spacing, and one coherent set of design tokens. This is a presentation change. Routes, data flow, API calls, i18n keys and business logic stay as they are, because the user asked for a new look, not new behavior, and silent behavior changes are the fastest way to lose their trust.

## Workflow

### 1. Survey before touching anything

Read, don't edit. You are looking for the things that decide how the redesign must be done:

- **Router and nav items**: where routes are registered (usually `main.js` or `router/`) and where the top nav links are rendered (usually `App.vue`). Note labels, whether they come from an i18n helper, and any active-link logic.
- **App shell**: everything `App.vue` renders around `<router-view>`: header, global filter bar, language switcher, profile menu, modals. Each of these needs a new home in the new layout; list them.
- **Styling approach**: global CSS in `App.vue`, scoped styles per component, Tailwind, a component library, or CSS variables already in use. Match it. Do not introduce Tailwind or a UI kit into a project that doesn't use one.
- **Existing design system**: check `CLAUDE.md`, a design doc, or existing CSS variables for palette, status colors and rules (for example "no emojis"). The project's palette wins over the defaults in this skill, because the redesign should look like the same product, only better organized.
- **Project conventions that affect how you edit**: for example, a `CLAUDE.md` rule that `.vue` files must be created or edited by a specific subagent, a component style (Options-style `setup()` vs `<script setup>`), required comments, and the test command. Follow them.

### 2. Plan the shell and confirm anything ambiguous

Decide, from the survey, where each existing header element goes (see the layout below). If the app has a global filter bar or other cross-page controls, say where you are putting them. Only ask the user when a choice changes behavior; otherwise pick the sensible default and state it in the final report.

### 3. Build the foundation: tokens

Create one place for design tokens as CSS variables on `:root` (global stylesheet or `App.vue` global block, wherever the project keeps global CSS). Everything you write after this uses tokens, never raw numbers, so the spacing and color stay consistent and a later change is a one-line edit. See `references/shell-templates.md` for a starting token set.

Principles that make the result look professional rather than merely rearranged:

- **A 4px spacing scale** (4, 8, 12, 16, 24, 32, 48). Inconsistent gaps are the most visible sign of an unpolished UI.
- **Few colors, used with intent**: a neutral ramp for surfaces/text/borders, one accent for primary actions and active nav, and the project's status colors (success/info/warning/danger) only for status.
- **Hairline borders and soft shadows** instead of heavy outlines; one radius scale (6/8/12).
- **A small type scale** (12/13/14/16/20/24) with 14px body text, and a clear page title.
- **Dark mode variants** under `@media (prefers-color-scheme: dark)`, by redefining the same tokens. Give `body` an explicit background so nothing renders as browser white or black.

### 4. Build the app shell

Layout (desktop):

```
+----------+------------------------------------------+
| Sidebar  | Top bar: page title | language | profile   |
| brand    +------------------------------------------+
| nav      | Toolbar: global filters (if the app has them)
| ...      +------------------------------------------+
| collapse | Content: max-width container, 24-32px padding
+----------+------------------------------------------+
```

- **Sidebar**: fixed, full height, 256px wide, brand at the top, nav items (icon + label) in the middle, collapse control at the bottom. Active item uses the accent tint and `router-link-active`/`aria-current="page"`. Group items under small section labels when there are more than about six.
- **Collapsible**: toggles to a 72px icon rail; labels hide, each item keeps a `title`/tooltip with its label. Persist the choice in `localStorage`, wrapped in try/catch because storage can be unavailable; the UI must work without it.
- **Mobile**: below roughly 1024px the sidebar becomes an off-canvas drawer opened by a hamburger in the top bar, with a backdrop, closing on route change, backdrop click and Escape.
- **Top bar**: page title (from route or the active nav label) on the left; utilities (language switcher, profile menu, anything that was in the old header) on the right.
- **Content**: one scrollable region with consistent padding and a max width, so wide tables don't stretch edge to edge on large monitors. Wide tables scroll inside their own container, never the whole page horizontally.
- **Accessibility**: `<nav aria-label>` landmark, visible `:focus-visible` rings, `aria-expanded` on the collapse and hamburger buttons, sufficient contrast in both themes, and respect `prefers-reduced-motion` for the slide/collapse transitions.

Use inline SVG icons (24x24, 1.75 stroke, round caps) unless the project already has an icon library. A new dependency for ten icons is not worth it. If the project forbids emojis, never use them as icons.

Extract the sidebar into its own component (and the collapse state into a small composable) rather than growing `App.vue`; the template file has working starting points.

### 5. Polish pass over the pages

With the shell in place, apply the tokens across the views so the whole app looks like one product. Change presentation only:

- A consistent **page header** (title + one-line description + optional actions) on every view.
- **Cards**: one surface color, hairline border, token radius and padding, consistent card header.
- **Tables**: comfortable row height, subtle header row, row hover, numeric columns right-aligned, consistent badge style for statuses.
- **Stat/KPI cards and grids**: shared grid gap, same card treatment.
- **Buttons and inputs**: one height scale, clear primary/secondary/disabled states, matching focus rings.
- Replace hardcoded colors, pixel gaps and font sizes with tokens as you touch each file. Don't rewrite component logic, rename props, or restructure data loading.

Work view by view and keep each view working before moving to the next, so a mistake is easy to localize.

### 6. Verify in a real browser

A redesign that builds can still be broken visually, so look at it:

1. Run the project's build (and its tests, if any) and fix failures.
2. Start the dev server and open every route. Check the browser console for new errors (pre-existing errors are not yours to fix, but mention them).
3. Take screenshots at desktop (about 1440px), tablet (about 900px) and phone (about 390px) widths, sidebar expanded and collapsed, and in dark mode if you added it. Use whatever browser tooling the project specifies (for example Playwright MCP).
4. Check: no horizontal page scroll, no text clipped or overlapping, active nav item highlights on the right route, drawer opens/closes on mobile, collapse state survives a reload, language switcher and profile menu still work, modals still layer above the sidebar (check `z-index`).

### 7. Report

Summarize for the user: the new layout and where each old header element moved, the tokens file location, which views were polished, what you verified (with the widths and themes you actually checked), and anything not verified or left out of scope. If you noticed unrelated bugs, list them separately rather than fixing them silently.

## Things that commonly go wrong

- **Sidebar covers content or content is double-padded.** Use one layout mechanism (CSS grid on the shell, or a fixed sidebar plus a matching content offset), not both.
- **`100vh` on mobile** clips content behind browser chrome; prefer `100dvh` with a `100vh` fallback.
- **Modals render behind the sidebar** because of `z-index` order. Define a small z-index scale in the tokens and use it everywhere.
- **Collapsed rail loses meaning**: keep icons recognizable and give every item a tooltip.
- **Scoped styles fight the new global tokens.** Update the scoped rules to use variables instead of adding `!important`.
- **Flash of wrong collapse state** on load: read the stored value synchronously before first render.

## Bundled reference

- `references/shell-templates.md`: starting-point token CSS, sidebar component, collapse composable, drawer behavior and icon guidance. Read it when you reach steps 3 and 4, then adapt it to the project's conventions instead of pasting it verbatim.
