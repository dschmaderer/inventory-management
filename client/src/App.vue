<template>
  <div class="app-shell" :class="{ collapsed: effectiveCollapsed, tablet: isTablet }">
    <AppSidebar
      :collapsed="effectiveCollapsed"
      :open="drawerOpen"
      @toggle-collapse="onToggleCollapse"
      @close="drawerOpen = false"
    />

    <div class="app-main">
      <!-- Top bar: hamburger (mobile) + page title on the left; language and profile on the right -->
      <header class="topbar">
        <button
          class="hamburger"
          type="button"
          aria-label="Open navigation"
          aria-controls="app-sidebar"
          :aria-expanded="drawerOpen"
          @click="drawerOpen = true"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="icons.menu"></svg>
        </button>
        <h1 class="topbar-title">{{ pageTitle }}</h1>
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>

      <!-- Global filters live in a toolbar directly under the top bar -->
      <FilterBar />

      <main class="content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppSidebar from './components/AppSidebar.vue'
import { useSidebar, navItems } from './composables/useSidebar'
import { icons } from './utils/icons'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    AppSidebar
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const { collapsed, toggle } = useSidebar()
    const route = useRoute()
    // Doubles as the phone drawer flag and the tablet overlay flag
    const drawerOpen = ref(false)

    // Tablet range (640-1023px): the sidebar is a 72px rail that expands into an
    // overlay. Read synchronously so the first paint already has the right mode.
    const TABLET_QUERY = '(min-width: 640px) and (max-width: 1023px)'
    const DESKTOP_QUERY = '(min-width: 1024px)'
    const supportsMedia = typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    const tabletMql = supportsMedia ? window.matchMedia(TABLET_QUERY) : null
    const desktopMql = supportsMedia ? window.matchMedia(DESKTOP_QUERY) : null
    const isTablet = ref(tabletMql ? tabletMql.matches : false)
    const isDesktop = ref(desktopMql ? desktopMql.matches : true)
    const onTabletChange = (event) => { isTablet.value = event.matches }
    const onDesktopChange = (event) => { isDesktop.value = event.matches }
    onMounted(() => {
      if (tabletMql) tabletMql.addEventListener('change', onTabletChange)
      if (desktopMql) desktopMql.addEventListener('change', onDesktopChange)
    })
    onBeforeUnmount(() => {
      if (tabletMql) tabletMql.removeEventListener('change', onTabletChange)
      if (desktopMql) desktopMql.removeEventListener('change', onDesktopChange)
    })

    // Tablet: rail when closed, expanded when open (never touches the persisted
    // value). Elsewhere: the persisted desktop value (ignored by phone CSS).
    const effectiveCollapsed = computed(() => (isTablet.value ? !drawerOpen.value : collapsed.value))

    const onToggleCollapse = () => {
      if (isTablet.value) drawerOpen.value = !drawerOpen.value
      else toggle()
    }

    // Crossing a breakpoint resets the overlay/drawer so no stale open state or
    // backdrop survives a resize
    watch([isTablet, isDesktop], () => { drawerOpen.value = false })

    // Page title = label of the nav item matching the current route
    const pageTitle = computed(() => {
      const item = navItems.find((entry) => entry.to === route.path)
      if (!item) return t('nav.companyName')
      return item.labelKey ? t(item.labelKey) : item.label
    })

    // Close the mobile drawer on navigation and on Escape
    watch(() => route.path, () => { drawerOpen.value = false })
    const onKeydown = (event) => {
      if (event.key === 'Escape') drawerOpen.value = false
    }
    onMounted(() => document.addEventListener('keydown', onKeydown))
    onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      effectiveCollapsed,
      isTablet,
      onToggleCollapse,
      drawerOpen,
      pageTitle,
      icons,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: var(--text-base);
  background: var(--bg);
  color: var(--text-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---------- App shell ---------- */

/* One layout mechanism: a grid whose first column is the sidebar. minmax(0, 1fr)
   lets wide tables scroll inside their own container instead of the page. */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  min-height: 100dvh;
  transition: grid-template-columns 0.2s ease;
}

.app-shell.collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
}

.app-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  height: var(--topbar-height);
  padding: 0 var(--space-6);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.topbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: none;
}

.hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  flex: none;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  cursor: pointer;
}

.hamburger svg {
  width: 20px;
  height: 20px;
}

.hamburger:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.hamburger:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

/* Tablet (640-1023px): permanent 72px rail column. The expanded sidebar is a
   fixed overlay that leaves the grid, so the column stays at rail width and the
   main column is pinned to column 2 (content never shifts). */
@media (min-width: 640px) and (max-width: 1023px) {
  .app-shell,
  .app-shell.collapsed {
    grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
  }

  .app-main {
    grid-column: 2;
  }
}

/* Phone (<640px): single column, sidebar is an off-canvas drawer */
@media (max-width: 639px) {
  .app-shell,
  .app-shell.collapsed {
    grid-template-columns: minmax(0, 1fr);
  }

  .hamburger {
    display: inline-flex;
  }
}

@media (max-width: 1023px) {
  .topbar {
    padding: 0 var(--space-4);
    gap: var(--space-3);
  }

  .content {
    padding: var(--space-4);
  }
}

/* ---------- Shared page styles ---------- */

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  /* auto-fit + minmax lets cards share the row evenly instead of leaving gaps */
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--warning); }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.danger .stat-value { color: var(--danger); }
.stat-card.info .stat-value { color: var(--info); }

.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  /* wrap so headers with a search box or legend never push the page wider on phones */
  flex-wrap: wrap;
  gap: var(--space-3);
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--bg);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-3);
  font-weight: 600;
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3);
  border-top: 1px solid var(--surface-hover);
  color: var(--text-body);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--bg);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  white-space: nowrap;
}

.badge.success,
.badge.increasing { background: var(--success-bg); color: var(--success-text); }

.badge.warning,
.badge.medium { background: var(--warning-bg); color: var(--warning-text); }

.badge.danger,
.badge.decreasing,
.badge.high { background: var(--danger-bg); color: var(--danger-text); }

.badge.info,
.badge.low { background: var(--info-bg); color: var(--info-text); }

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--text-muted);
  font-size: var(--text-base);
}

.error {
  background: #fef2f2;
  border: 1px solid var(--danger-bg);
  color: var(--danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}

/* Shared button styles for opt-in use by views */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: var(--control-height);
  padding: 0 var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-strong);
  background: var(--surface);
  color: var(--text-body);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.btn:hover:not(:disabled) { background: var(--surface-hover); }
.btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
</style>
