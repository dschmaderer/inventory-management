<template>
  <!-- Backdrop only renders visibly in drawer mode (below 1024px, see CSS) -->
  <div v-if="open" class="sidebar-backdrop" @click="$emit('close')"></div>
  <aside id="app-sidebar" class="sidebar" :class="{ open, collapsed }">
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true">C</div>
      <div class="brand-text">
        <div class="brand-name">{{ t('nav.companyName') }}</div>
        <div class="brand-sub">{{ t('nav.subtitle') }}</div>
      </div>
      <!-- Close button is only shown in drawer mode -->
      <button class="drawer-close" type="button" aria-label="Close navigation" @click="$emit('close')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="icons.close"></svg>
      </button>
    </div>

    <nav class="sidebar-nav" aria-label="Main">
      <router-link
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :title="collapsed ? item.label : null"
        :aria-label="collapsed ? item.label : null"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="icons[item.icon]"></svg>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <button
      class="collapse-btn"
      type="button"
      :aria-expanded="!collapsed"
      :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      aria-label="Toggle sidebar"
      @click="$emit('toggle-collapse')"
    >
      <svg class="collapse-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="icons.chevronLeft"></svg>
      <span class="nav-label">Collapse</span>
    </button>
  </aside>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import { navItems } from '../composables/useSidebar'
import { icons } from '../utils/icons'

export default {
  name: 'AppSidebar',
  props: {
    collapsed: { type: Boolean, default: false },
    open: { type: Boolean, default: false }
  },
  emits: ['toggle-collapse', 'close'],
  setup() {
    const { t } = useI18n()

    // Resolve labels reactively so the language switcher updates the nav
    const items = computed(() =>
      navItems.map((item) => ({
        ...item,
        label: item.labelKey ? t(item.labelKey) : item.label
      }))
    )

    return { t, items, icons }
  }
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: var(--space-4) var(--space-3);
  z-index: var(--z-sidebar);
  overflow: hidden;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  padding: 0 var(--space-2);
  margin-bottom: var(--space-6);
}

.brand-mark {
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--text-md);
}

.brand-text {
  min-width: 0;
}

.brand-name {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-sub {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.drawer-close {
  display: none;
  margin-left: auto;
  flex: none;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
}

.drawer-close svg {
  width: 20px;
  height: 20px;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
}

.nav-item,
.collapse-btn {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  text-decoration: none;
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  white-space: nowrap;
  background: none;
  border: none;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-item:hover,
.collapse-btn:hover {
  background: var(--surface-hover);
  color: var(--text);
}

/* "/" would match every route with the non-exact class, so use exact-active */
.nav-item.router-link-exact-active,
.nav-item[aria-current='page'] {
  background: var(--accent-tint);
  color: var(--accent);
}

.nav-item:focus-visible,
.collapse-btn:focus-visible,
.drawer-close:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.nav-icon,
.collapse-icon {
  width: 20px;
  height: 20px;
  flex: none;
}

.collapse-btn {
  margin-top: var(--space-3);
  border-top: 1px solid var(--border);
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  height: 48px;
}

.collapse-icon {
  transition: transform 0.2s ease;
}

/* Icon rail: hide text, center icons, flip the chevron */
.sidebar.collapsed .nav-label,
.sidebar.collapsed .brand-text {
  display: none;
}

.sidebar.collapsed .nav-item,
.sidebar.collapsed .collapse-btn {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .collapse-icon {
  transform: rotate(180deg);
}

/* Backdrop (phone drawer and tablet overlay) */
@media (max-width: 1023px) {
  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    background: rgb(15 23 42 / 0.4);
    z-index: var(--z-backdrop);
  }
}

/* Phone drawer mode (<640px) */
@media (max-width: 639px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-width);
    max-width: 85vw;
    transform: translateX(-100%);
    /* visibility keeps off-screen links out of the tab order once closed */
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0s linear 0.2s;
    z-index: var(--z-drawer);
    box-shadow: var(--shadow-lg);
  }

  .sidebar.open {
    transform: none;
    visibility: visible;
    transition: transform 0.2s ease;
  }

  .drawer-close {
    display: inline-flex;
  }

  /* Collapsed state is meaningless in a drawer: always show labels */
  .sidebar.collapsed .nav-label,
  .sidebar.collapsed .brand-text {
    display: block;
  }

  .sidebar.collapsed .nav-item,
  .sidebar.collapsed .collapse-btn {
    justify-content: flex-start;
    padding: 0 var(--space-3);
  }

  .sidebar.collapsed .sidebar-brand {
    justify-content: flex-start;
    padding: 0 var(--space-2);
  }

  .sidebar.collapsed .collapse-icon {
    transform: none;
  }

  /* The collapse control does nothing useful in the drawer */
  .collapse-btn {
    display: none;
  }
}

/* Tablet (640-1023px): the rail stays in the grid; when open (not collapsed) the
   sidebar is lifted out of the flow as a fixed overlay above the top bar. */
@media (min-width: 640px) and (max-width: 1023px) {
  .sidebar.open {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-width);
    max-width: 85vw;
    z-index: var(--z-drawer);
    box-shadow: var(--shadow-lg);
  }
}

@media (min-width: 1024px) {
  .sidebar-backdrop {
    display: none;
  }
}
</style>
