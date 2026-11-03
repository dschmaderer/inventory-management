# CLAUDE.md

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Quick Start

```bash
# Backend
cd server
uv run python main.py

# Frontend
cd client
npm install && npm run dev
```

## Commands

```bash
./scripts/start.sh                # start both servers (./scripts/stop.sh to stop)
cd server && uv sync              # install backend deps (incl. pytest dev group)
cd client && npm run build        # production build -> client/dist/ (no lint or frontend tests exist)

# Backend tests (67 tests, run from tests/ so pytest.ini is picked up)
cd tests && uv run --project ../server pytest backend -v
cd tests && uv run --project ../server pytest backend/test_restock.py::<test_name> -v   # single test
```

Python >=3.11, Node ^20.19 or >=22.12. `server/generate_data.py` regenerates sample JSON (all dates in 2025).

## Architecture Notes

- `server/main.py` holds all routes and Pydantic models in one file. `server/mock_data.py` loads `server/data/*.json` into module-level lists at import. The only write endpoint is `POST /api/restock-orders`, which appends to the in-memory `restock_orders` list (resets on restart); everything else is read-only.
- Restocking: `/api/restock/recommendations?budget=` ranks forecast items by trend, then shortfall (`forecasted_demand` minus summed `quantity_on_hand`, 0 if the SKU is not in inventory) and fills the budget. Cost and category come from `server/data/restock_catalog.json` because `inventory.json` covers only 1 of the 9 forecast SKUs. Lead time is fixed per category (`LEAD_TIME_DAYS` in `main.py`); an order's lead time is its slowest item. The server recomputes prices on submit and never trusts client totals.
- Shared filtering lives in `apply_filters()` (warehouse/category/status, `'all'` = skip) and `filter_by_month()` in `main.py`. `month` accepts `YYYY-MM` or `Q1-2025`..`Q4-2025` (hardcoded `QUARTER_MAP`) and substring-matches `order_date`. Reuse these instead of writing new filter code.
- `client/src/composables/useFilters.js` keeps filter state in module-level refs (singleton shared by all views). Its names differ from the API params: `selectedLocation` -> `warehouse`, `selectedPeriod` -> `month`. `getCurrentFilters()` does the mapping.
- `client/src/api.js` is the only HTTP layer. It hardcodes `http://localhost:8001/api` and drops params equal to `'all'`; new endpoints need a method here.
- i18n: `useI18n.js` with `locales/en.js` and `locales/ja.js`. Locale persists in localStorage and also selects currency (en -> USD, ja -> JPY, see `utils/currency.js`). New UI strings need keys in both locale files.
- Routes are registered in `client/src/main.js`. `views/Backlog.vue` has no route and is not in the router.
- `useAuth.js` and the profile/tasks modals are client-side demo state with no backend.
- Subdirectory `client/CLAUDE.md` and `server/CLAUDE.md` contain generic Vue/FastAPI guidance; their examples (e.g. `models.py`, `services/`) describe suggested structure, not what exists today.

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions
- `GET /api/reports/quarterly`, `/api/reports/monthly-trends` - No filters
- `GET /api/restock/recommendations?budget=` - Budget-fitted restock list
- `POST /api/restock-orders`, `GET /api/restock-orders` - Submit / list restock orders (in-memory)

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## File Locations
- Views: `client/src/views/*.vue`
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Styles: `client/src/App.vue`

## Code Comments
- Always document non-obvious logic changes with comments (explain the why; skip self-evident code)

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
