# Shell templates

Starting points for the SaaS redesign. Adapt names, palette and component style (Options-style `setup()` vs `<script setup>`) to the project; these are not meant to be pasted unchanged.

Contents: tokens, shell layout, Sidebar component, collapse composable, icons, checklist.

## Tokens

Put in the project's global CSS. If the project already defines a palette (check `CLAUDE.md` or existing variables), map these token names onto its colors rather than introducing new hues.

```css
:root {
  /* Spacing: 4px base */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px; --space-12: 48px;

  /* Radius and elevation */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgb(15 23 42 / 0.06);
  --shadow-md: 0 4px 12px rgb(15 23 42 / 0.08);

  /* Type */
  --text-xs: 12px; --text-sm: 13px; --text-base: 14px; --text-md: 16px;
  --text-lg: 20px; --text-xl: 24px;

  /* Neutrals (slate) */
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-hover: #f1f5f9;
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #64748b;

  /* Accent and status */
  --accent: #2563eb;
  --accent-tint: #eff6ff;
  --success: #16a34a; --info: #2563eb; --warning: #d97706; --danger: #dc2626;

  /* Shell dimensions */
  --sidebar-width: 256px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 56px;

  /* z-index scale: keep modals above the shell */
  --z-sidebar: 30; --z-backdrop: 40; --z-drawer: 50; --z-modal: 100;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b1220; --surface: #111a2e; --surface-hover: #1a2540;
    --border: #243049; --text: #e2e8f0; --text-muted: #94a3b8;
    --accent: #60a5fa; --accent-tint: #1e2a4a;
    --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.4);
    --shadow-md: 0 4px 12px rgb(0 0 0 / 0.5);
  }
}

body { background: var(--bg); color: var(--text); font-size: var(--text-base); }

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
```

## Shell layout

Use CSS grid on the shell so the content never needs a manual offset:

```vue
<div class="app-shell" :class="{ collapsed }">
  <Sidebar :collapsed="collapsed" :open="drawerOpen" @toggle-collapse="toggle" @close="drawerOpen = false" />
  <div class="app-main">
    <header class="topbar">
      <button class="icon-btn hamburger" aria-label="Open navigation" :aria-expanded="drawerOpen" @click="drawerOpen = true">...</button>
      <h1 class="topbar-title">{{ pageTitle }}</h1>
      <div class="topbar-actions"><!-- language switcher, profile menu --></div>
    </header>
    <div class="toolbar"><!-- global filter bar, if the app has one --></div>
    <main class="content"><router-view /></main>
  </div>
</div>
```

```css
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr); /* minmax(0) lets wide tables scroll inside */
  min-height: 100vh;
  min-height: 100dvh;
  transition: grid-template-columns 0.2s ease;
}
.app-shell.collapsed { grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr); }

.topbar {
  position: sticky; top: 0; z-index: var(--z-sidebar);
  display: flex; align-items: center; gap: var(--space-4);
  height: var(--topbar-height); padding: 0 var(--space-6);
  background: var(--surface); border-bottom: 1px solid var(--border);
}
.topbar-title { font-size: var(--text-md); font-weight: 600; margin: 0; }
.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: var(--space-3); }
.hamburger { display: none; }

.content { padding: var(--space-6) var(--space-8); max-width: 1440px; width: 100%; margin: 0 auto; }

@media (max-width: 1023px) {
  .app-shell, .app-shell.collapsed { grid-template-columns: minmax(0, 1fr); }
  .hamburger { display: inline-flex; }
  .content { padding: var(--space-4); }
}
```

## Sidebar component

```vue
<template>
  <!-- Backdrop only matters in drawer mode (mobile) -->
  <div v-if="open" class="sidebar-backdrop" @click="$emit('close')"></div>
  <aside class="sidebar" :class="{ open, collapsed }">
    <div class="sidebar-brand">
      <!-- logo mark + app name; hide the name when collapsed -->
    </div>
    <nav class="sidebar-nav" aria-label="Main">
      <!-- one section label per group, hidden when collapsed -->
      <router-link
        v-for="item in items" :key="item.to" :to="item.to"
        class="nav-item" :title="collapsed ? item.label : null"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
             v-html="item.icon"></svg>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
    <button class="collapse-btn" :aria-expanded="!collapsed" @click="$emit('toggle-collapse')">
      <!-- chevron icon rotated when collapsed; label hidden when collapsed -->
    </button>
  </aside>
</template>
```

Build `items` from the app's existing nav links so labels keep using the project's i18n helper. `v-html` here is safe only because the icon strings are static constants in your own code; never feed it user or API data.

```css
.sidebar {
  position: sticky; top: 0; height: 100vh; height: 100dvh;
  display: flex; flex-direction: column;
  background: var(--surface); border-right: 1px solid var(--border);
  padding: var(--space-4) var(--space-3);
  z-index: var(--z-sidebar); overflow: hidden;
}
.nav-item {
  display: flex; align-items: center; gap: var(--space-3);
  height: 40px; padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--text-muted); text-decoration: none; font-weight: 500;
}
.nav-item:hover { background: var(--surface-hover); color: var(--text); }
.nav-item.router-link-exact-active,
.nav-item[aria-current="page"] { background: var(--accent-tint); color: var(--accent); }
.nav-item:focus-visible, .collapse-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.nav-icon { width: 20px; height: 20px; flex: none; }

.sidebar.collapsed .nav-label,
.sidebar.collapsed .sidebar-section-label { display: none; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 0; }

/* Drawer mode */
@media (max-width: 1023px) {
  .sidebar {
    position: fixed; inset: 0 auto 0 0; width: var(--sidebar-width);
    transform: translateX(-100%); transition: transform 0.2s ease;
    z-index: var(--z-drawer);
  }
  .sidebar.open { transform: none; }
  /* Collapsed state is meaningless in a drawer: always show labels */
  .sidebar.collapsed .nav-label { display: inline; }
  .sidebar-backdrop { position: fixed; inset: 0; background: rgb(15 23 42 / 0.4); z-index: var(--z-backdrop); }
}
```

Note: use `router-link-exact-active` for the Overview/home route (`/`), otherwise it matches every route and stays highlighted.

## Collapse composable

State at module level (shared singleton, like other composables in many Vue apps), read synchronously so the first paint is already correct. Storage can throw, so every access is wrapped.

```js
import { ref, watch } from 'vue'

const KEY = 'sidebar-collapsed'

const read = () => {
  try { return localStorage.getItem(KEY) === '1' } catch { return false }
}

const collapsed = ref(read())

watch(collapsed, (value) => {
  try { localStorage.setItem(KEY, value ? '1' : '0') } catch { /* storage unavailable: UI still works */ }
})

export function useSidebar() {
  const toggle = () => { collapsed.value = !collapsed.value }
  return { collapsed, toggle }
}
```

Drawer behavior (in the shell component): keep `drawerOpen` as local state; close it on route change (`watch(() => route.path, ...)`), on Escape (keydown listener added in `onMounted`, removed in `onBeforeUnmount`), and on backdrop click.

## Icons

Hand-written inline SVG path strings, 24x24 viewBox, stroke only. Keep them in a small `icons.js` constants file. A few simple shapes that render reliably:

```js
export const icons = {
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  list: '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
  trend: '<path d="m3 17 6-6 4 4 8-8M15 7h6v6"/>',
  box: '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5M12 13v8"/>'
}
```

Render each icon once in the browser and look at it; if one looks off, simplify it rather than guessing at path syntax. Choose icons by meaning (inventory = box, orders = list, finance = chart, forecast = trend).

## Checklist before reporting done

- Every old header element has a new home and still works (nav links, language switcher, profile menu, filter bar, modals).
- Tokens file exists and new/edited styles use variables, not literals.
- Verified at desktop, tablet and phone widths; collapsed and expanded; dark mode if added.
- No new console errors; build and existing tests pass.
