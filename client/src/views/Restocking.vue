<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
      <p class="filters-note">{{ t('restocking.globalFiltersNote') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-row">
        <label for="restock-budget" class="budget-label">{{ t('restocking.budget') }}</label>
        <input
          id="restock-budget"
          class="budget-slider"
          type="range"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          v-model.number="budget"
        />
        <div class="budget-readout">{{ formatMoney(budget) }}</div>
      </div>
    </div>

    <div v-if="confirmation" class="confirmation" role="status">
      <div class="confirmation-title">{{ t('restocking.confirmation.title') }}</div>
      <div class="confirmation-body">
        <span>{{ t('restocking.confirmation.orderNumber') }}: <strong>{{ confirmation.order_number }}</strong></span>
        <span>{{ t('restocking.confirmation.expectedDelivery') }}: <strong>{{ formatDate(confirmation.expected_delivery) }}</strong></span>
        <router-link to="/orders" class="confirmation-link">{{ t('restocking.confirmation.viewOrders') }}</router-link>
      </div>
    </div>

    <div v-if="loading && rows.length === 0" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="rows.length === 0" class="card empty-state">{{ t('restocking.empty') }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.orderTotal') }}</div>
          <div class="stat-value">{{ formatMoney(orderTotal) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ formatMoney(budget) }}</div>
        </div>
        <div :class="['stat-card', isOverBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
          <div class="stat-value">{{ formatMoney(remainingBudget) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.leadTime') }}</div>
          <div class="stat-value">{{ t('restocking.summary.days', { count: orderLeadTime }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.onHand') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.sku" :class="{ excluded: effectiveQuantity(row) === 0 }">
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ translateProductName(row.name) }}</td>
                <td>
                  <span :class="['badge', row.trend]">{{ trendLabel(row.trend) }}</span>
                </td>
                <td class="num">{{ row.on_hand.toLocaleString() }}</td>
                <td class="num">{{ row.shortfall.toLocaleString() }}</td>
                <td class="num">
                  <input
                    class="qty-input"
                    type="number"
                    step="1"
                    min="0"
                    :max="row.shortfall"
                    :aria-label="t('restocking.table.quantity') + ' ' + row.sku"
                    v-model.number="row.quantity"
                    @change="normalizeQuantity(row)"
                  />
                </td>
                <td class="num">{{ formatMoney(row.unit_cost, 2) }}</td>
                <td class="num"><strong>{{ formatMoney(lineTotal(row), 2) }}</strong></td>
                <td class="num">{{ row.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="isOverBudget" class="warning-banner" role="alert">{{ t('restocking.overBudget') }}</div>
      <div v-if="orderError" class="error" role="alert">{{ orderError }}</div>

      <div class="actions">
        <span class="actions-count">{{ t('restocking.summary.itemsIncluded') }}: {{ includedItems.length }}</span>
        <button class="place-order" type="button" :disabled="!canPlaceOrder" @click="placeOrder">
          {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_MIN = 0
const BUDGET_MAX = 60000
const BUDGET_STEP = 500
const DEBOUNCE_MS = 300

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    // NOTE: the global filters (useFilters: period, warehouse, category, status)
    // intentionally do NOT apply here; recommendations depend only on the budget.

    const budget = ref(20000)
    const rows = ref([]) // recommended items; `quantity` is editable per row
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const orderError = ref(null)
    const confirmation = ref(null)

    // Monotonic id so a slow response for an old budget can't overwrite a newer one
    let requestSeq = 0
    let debounceTimer = null

    const formatMoney = (amount, decimals = 0) => {
      return formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const trendLabel = (trend) => {
      const key = `trends.${trend}`
      const label = t(key)
      return label === key ? trend : label
    }

    // Quantity as an integer within [0, shortfall]; blank/invalid input counts as 0
    const effectiveQuantity = (row) => {
      const q = Math.floor(Number(row.quantity))
      if (!Number.isFinite(q) || q < 0) return 0
      return Math.min(q, row.shortfall)
    }

    const normalizeQuantity = (row) => {
      row.quantity = effectiveQuantity(row)
    }

    const lineTotal = (row) => effectiveQuantity(row) * row.unit_cost

    // Rows with quantity 0 are excluded from the order
    const includedItems = computed(() => rows.value.filter(row => effectiveQuantity(row) > 0))

    const orderTotal = computed(() => {
      return includedItems.value.reduce((sum, row) => sum + lineTotal(row), 0)
    })

    // Small epsilon so float rounding on cents never causes a false over-budget state
    const isOverBudget = computed(() => orderTotal.value > budget.value + 0.005)

    const remainingBudget = computed(() => budget.value - orderTotal.value)

    // Order lead time is driven by the slowest included item
    const orderLeadTime = computed(() => {
      return includedItems.value.reduce((max, row) => Math.max(max, row.lead_time_days), 0)
    })

    const canPlaceOrder = computed(() => {
      // confirmation blocks re-submit: a second click would create a duplicate order
      return !loading.value && !placing.value && !confirmation.value &&
        includedItems.value.length > 0 && !isOverBudget.value
    })

    const loadRecommendations = async () => {
      const seq = ++requestSeq
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockRecommendations(budget.value)
        if (seq !== requestSeq) return // stale response, a newer request is in flight
        rows.value = data.items.map(item => ({ ...item }))
      } catch (err) {
        if (seq !== requestSeq) return
        rows.value = []
        error.value = t('restocking.loadError') + ': ' + err.message
        console.error('Load error:', err)
      } finally {
        // Only the latest request controls the loading flag
        if (seq === requestSeq) loading.value = false
      }
    }

    // Debounce slider movement; flag loading immediately so Place Order is disabled meanwhile
    watch(budget, () => {
      confirmation.value = null
      loading.value = true
      // Invalidate any in-flight response for the old budget so it can't replace rows
      // or clear `loading` during the debounce window; the next loadRecommendations
      // call (which bumps the seq again) then owns `loading`.
      requestSeq++
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    })

    // Any change to the effective quantities means the order differs from the one
    // just confirmed, so re-enable Place Order by clearing the confirmation.
    watch(
      () => rows.value.map(effectiveQuantity).join(','),
      () => { confirmation.value = null }
    )

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      try {
        placing.value = true
        orderError.value = null
        confirmation.value = null
        const result = await api.createRestockOrder({
          budget: budget.value,
          items: includedItems.value.map(row => ({
            sku: row.sku,
            quantity: effectiveQuantity(row)
          }))
        })
        confirmation.value = result
      } catch (err) {
        // Backend returns { detail } on validation errors
        const detail = err.response && err.response.data && err.response.data.detail
        const message = typeof detail === 'string' ? detail : (detail ? JSON.stringify(detail) : err.message)
        orderError.value = t('restocking.orderFailed') + ': ' + message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)
    onBeforeUnmount(() => {
      clearTimeout(debounceTimer)
      requestSeq++ // invalidate any in-flight request
    })

    return {
      t,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      budget,
      rows,
      loading,
      error,
      placing,
      orderError,
      confirmation,
      includedItems,
      orderTotal,
      remainingBudget,
      orderLeadTime,
      isOverBudget,
      canPlaceOrder,
      effectiveQuantity,
      normalizeQuantity,
      lineTotal,
      formatMoney,
      formatDate,
      trendLabel,
      translateProductName,
      placeOrder
    }
  }
}
</script>

<style scoped>
.filters-note {
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: #94a3b8;
}

.budget-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-label {
  font-weight: 600;
  color: #0f172a;
}

.budget-slider {
  flex: 1;
  accent-color: #2563eb;
}

.budget-readout {
  min-width: 110px;
  text-align: right;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.empty-state {
  text-align: center;
  color: #64748b;
  padding: 2rem;
}

.num {
  text-align: right;
}

.qty-input {
  width: 80px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  text-align: right;
  font-size: 0.875rem;
  color: #0f172a;
}

.qty-input:focus {
  outline: 2px solid #bfdbfe;
  border-color: #2563eb;
}

.excluded td {
  color: #94a3b8;
}

.warning-banner {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #92400e;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.938rem;
}

.actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
}

.actions-count {
  color: #64748b;
  font-size: 0.875rem;
}

.place-order {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.625rem 1.5rem;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
}

.place-order:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.confirmation {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
}

.confirmation-title {
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.confirmation-body {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  font-size: 0.938rem;
}

.confirmation-link {
  color: #1d4ed8;
  font-weight: 600;
}
</style>
