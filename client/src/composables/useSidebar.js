import { ref, watch } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'

// Storage can be unavailable (privacy mode, blocked cookies), so every access
// is wrapped; the sidebar still works, it just won't remember its state.
const readStored = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch (err) {
    return false
  }
}

// Module-level singleton, read synchronously so the first paint already has
// the right width (no flash of the wrong collapse state).
const collapsed = ref(readStored())

watch(collapsed, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
  } catch (err) {
    // Ignore: persistence is a nicety, not a requirement
  }
})

// Single source of truth for nav entries, shared by the sidebar and the top
// bar title. `labelKey` is an i18n key; "Reports" has no key so it keeps its
// hardcoded English `label`.
export const navItems = [
  { to: '/', labelKey: 'nav.overview', icon: 'grid' },
  { to: '/inventory', labelKey: 'nav.inventory', icon: 'box' },
  { to: '/orders', labelKey: 'nav.orders', icon: 'list' },
  { to: '/spending', labelKey: 'nav.finance', icon: 'chart' },
  { to: '/demand', labelKey: 'nav.demandForecast', icon: 'trend' },
  { to: '/restocking', labelKey: 'nav.restocking', icon: 'restock' },
  { to: '/reports', label: 'Reports', icon: 'file' }
]

export function useSidebar() {
  const toggle = () => {
    collapsed.value = !collapsed.value
  }
  return { collapsed, toggle, navItems }
}
