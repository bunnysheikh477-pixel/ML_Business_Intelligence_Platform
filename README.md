# ML Business Intelligence Platform

A full-stack ML-powered Business Intelligence platform with a FastAPI backend, MongoDB storage, and a Next.js (App Router) frontend. The platform ingests CSV/XLSX datasets, computes real-time KPIs, generates interactive Plotly charts in Python, and runs sales forecasting with honest baseline evaluation.

## Features

- **Dataset Management** – Upload CSV/XLSX (validated, profiled), list/review datasets, preview rows, column-level data profiling (dtypes, missing %, unique, duplicates). Bundled sample dataset via `POST /api/v1/datasets/sample`.
- **BI Analytics** – Automatic column detection (date/revenue/order/category/region/product/profit/quantity), flexible filters (date range, category, region), accurate KPIs (revenue, profit/margin, orders/AOV, quantity), monthly/category/region/product aggregations, and data quality summaries.
- **Interactive Charts** – Python-generated Plotly figures (monthly revenue trend, sales by category/region, top products, profit vs revenue, missing values). API returns serialized figures consumed by a lazy-loaded `plotly.js-dist` frontend component. Responses are cached in-process (TTL) by dataset signature + query.
- **Sales Forecasting (ML)** – Linear trend model with chronological holdout evaluation against a naive last-value baseline. Reports MAE/RMSE/MAPE (MAPE computed only over non-zero actuals), comparison and warnings. Negative raw predictions are clamped to 0 and flagged. Produces an "actual vs predicted + forecast" Plotly figure.
- **Frontend Shell** – Single-page Next.js app (App Router, React 19, TypeScript, Tailwind) with sidebar nav (Overview, Datasets, Analytics, ML predictions, Reports). All metrics render from live API calls (no fabricated/sample numbers in the UI except the bundled dataset). Charts are loaded dynamically.
- **Robust Ingestion** – CSV decoding with multiple encodings (utf-8-sig/utf-8/cp1252), XLSX via openpyxl, validation (size/extension/empty/column names/duplicates/row/column limits), safe JSON serialization of pandas values.

## Architecture

| Layer | Tech | Notes |
|---|---|---|
| Backend | FastAPI, Uvicorn | API prefix `/api/v1`, CORS, health endpoint (`/health/database`) |
| DB | MongoDB (Atlas) | Stores dataset metadata (file path, sizes, counts, columns, stored preview/profile, timestamps). Files stored on disk under `backend/storage/uploads/`. |
| Data | pandas, openpyxl | CSV/XLSX ingestion, normalization, profiling, aggregations |
| ML | scikit-learn, numpy | LinearRegression, chronological holdout, naive baseline, metrics (MAE/RMSE/MAPE) |
| Charts | Plotly 7.1.0 | Serialized JSON figures returned by API; frontend uses `plotly.js-dist@3.7.0` (lazy/dynamic import, code-split) |
| Frontend | Next.js 15 (App Router), React 19, TypeScript, Tailwind | Typed API client, reusable UI, views per section, responsive + print-friendly report view |

## Prerequisites

- Python 3.10 (venv at `backend/venv`)
- Node.js 18+ (tested with current LTS)
- MongoDB Atlas cluster with network access (or local MongoDB) — connection string required
- Windows (paths shown use Windows; commands are cross-platform with minor adjustments)

## Project Structure

```
ML_Business_Intelligence_Platform/
├── backend/
│   ├── app/
│   │   ├── analytics/        # column detection, filters, KPIs, aggregations
│   │   ├── api/v1/           # routers: datasets, analytics, charts, ml
│   │   ├── charts/           # Plotly chart builders + forecast figure
│   │   ├── core/             # config, in-process TTL cache
│   │   ├── db/               # MongoDB connection
│   │   ├── ingestion/        # CSV/XLSX readers + validator
│   │   ├── ml/               # sales forecasting (trend + baseline + eval)
│   │   ├── services/         # dataset service (upload/list/details/preview/profile)
│   │   └── main.py           # FastAPI app + CORS + routers + health
│   ├── tests/                # pytest: analytics, charts, datasets, forecasting, api
│   ├── storage/uploads/      # stored dataset files (.gitkeep)
│   ├── .env.example          # backend env template
│   ├── pytest.ini             # pythonpath=.
│   ├── requirements.txt      # backend deps (includes pymongo/dnspython/plotly/pytest)
│   └── sample_sales.csv      # bundled sample (153 rows, 21 months; original 10 preserved)
├── frontend/
│   └── ml-bi-platform/
│       ├── app/              # App Router (page.tsx, globals.css)
│       ├── components/       # PlotlyChart, UI kit, ChartCard, UploadForm, views/*
│       ├── lib/              # api client, useAsync, csv helpers
│       ├── types/            # ambient Plotly typings
│       ├── .env.example
│       ├── next.config.ts
│       ├── package.json
│       └── tsconfig.json
└── README.md
```

## 1) Backend Setup

### Create/activate venv (Windows PowerShell shown)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Install dependencies
```powershell
pip install -r requirements.txt
```
Key packages: `fastapi`, `uvicorn[standard]`, `pandas`, `openpyxl`, `pymongo`, `dnspython`, `plotly`, `scikit-learn`, `numpy`, `python-dotenv`, `python-multipart`, `httpx`, `pytest`.

### Environment variables
Copy `.env.example` → `.env` and fill values:
```env
MONGODB_URL=mongodb+srv://<user>:<password>@<cluster-host>/?retryWrites=true&w=majority
MONGODB_DATABASE=ml_bi_platform
GEMINI_API_KEY=  # optional
UPLOAD_DIR=storage/uploads
MAX_UPLOAD_SIZE_MB=20
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CHART_CACHE_TTL_SECONDS=60
SAMPLE_DATASET_PATH=sample_sales.csv
```
MongoDB: ensure Atlas IP allowlist includes your IP (or `0.0.0.0/0` for local dev only). `db.command("ping")` is used for `/health/database`.

### Storage
`storage/uploads/` holds stored dataset files. Filenames are UUID-based; original names preserved in metadata. `.gitkeep` present.

### Run backend (dev)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```
Docs: http://localhost:8000/docs  |  Health: http://localhost:8000/health/database

### Run tests
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
```
Expected: **80 passed**.

## 2) Frontend Setup

```powershell
cd frontend/ml-bi-platform
npm install
cp .env.example .env.local  # or .env
```

`.env.example`:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```
Fallbacks: `NEXT_PUBLIC_API_BASE_URL` → `NEXT_PUBLIC_API_URL` → `http://localhost:8000/api/v1`.

Scripts (package.json): `dev`, `build`, `start`, `lint`.

### Dev
```powershell
npm run dev
```
http://localhost:3000

### Build & Start (production)
```powershell
npm run build
npm run start
```
Plotly is dynamically imported and code-split (~4.5 MB lazy chunk); initial First Load JS ~122 KB.

### Typecheck
```powershell
npx tsc --noEmit
```

## 3) API Endpoints (v1, prefix `/api/v1`)

### Health
- `GET /health/database` – returns `{database:"connected", type:"MongoDB"}` or 503

### Datasets (`/datasets`)
| Method | Path | Notes |
|---|---|---|
| `POST` | `/datasets/upload` | multipart `file` (.csv/.xlsx, ≤20MB). Validates, parses, profiles, stores file + metadata in MongoDB. Returns `{success, dataset}`. |
| `POST` | `/datasets/sample` | Loads bundled `sample_sales.csv`. Idempotent if identical copy exists (by name+row_count). Returns `{success, dataset}`. |
| `GET` | `/datasets/` | Lists datasets (newest first, limit 100). `{success, datasets}`. |
| `GET` | `/datasets/{dataset_id}` | Details: metadata + detected column roles + filters flags + stored profile. `{success, dataset}`. |
| `GET` | `/datasets/{dataset_id}/preview?limit={1..100}` | First N rows (JSON-safe). `{success, data: {dataset_id,name,columns,rows}}`. |
| `GET` | `/datasets/{dataset_id}/profile` | Column profile + row/col counts + duplicates. `{success, profile}`. |

### Analytics (`/analytics`)
| Method | Path | Notes |
|---|---|---|
| `GET` | `/analytics/{dataset_id}/overview` | KPIs, monthly/category/region/top-products, detected columns, available columns, facets (category/region), rows_analyzed, warnings. Query params (all optional): `revenue_column|sales_column`, `order_id_column`, `date_column`, `category_column`, `region_column`, `profit_column`, `quantity_column`, `product_column`, `date_from`, `date_to` (ISO dates), `category_value`, `region_value`. |

### Charts (`/charts`)
| Method | Path | Notes |
|---|---|---|
| `GET` | `/charts/{dataset_id}` | Returns all charts in order: `monthly_revenue`, `sales_by_category`, `sales_by_region`, `top_products`, `profit_vs_revenue`, `missing_values`. Each chart: `{key,title,description,type,status,reason?,figure?}` where `figure = {data,layout}` (Plotly JSON). Cached (TTL) by dataset signature + query. Same mapping/filter query params as above. Returns `{success,cached,dataset,detected_columns,available_columns,filters,charts,warnings}`. |
| `GET` | `/charts/{dataset_id}/{chart_key}` | Single chart. Valid keys from `CHART_BUILDERS`. Same query params. Returns `{success,dataset,detected_columns,filters,warnings,chart}`. |

Charts behavior: builders degrade gracefully (return `status:"unavailable"` with `reason` if data/columns insufficient). `missing_values` returns unavailable when no missing values exist.

### ML (`/ml`)
| Method | Path | Notes |
|---|---|---|
| `POST` | `/ml/{dataset_id}/forecast?periods={1..12}` | Optional query: `date_column`, `sales_column`. Aggregates to monthly, fits `LinearRegression` on full history, runs chronological holdout vs `naive_last_value` (baseline = last training month value). Returns `{success,dataset_id,dataset,columns,data,figure}`. `data` includes: `model`, `baseline`, `target`, `date_column`, `frequency`, `historical_months`, `history[{month,actual_sales}]`, `forecasts[{month,predicted_sales,raw_prediction}]`, `evaluation` (`evaluated` or `insufficient_data`), `warnings[]`, `notes[]`, `warning` (legacy). Negative raw predictions clamped to 0; clamping recorded in warnings. MAPE only over non-zero actuals. Figure is "actual vs predicted + forecast". |

## 4) Implementation Notes

### Column Detection
Normalization (case-insensitive, strip accents/punctuation, collapse spaces, fuzzy substring fallback) with role candidates. Explicit column requests override detection and raise clear errors listing available columns.

### Filtering & Facets
Date/category/region filters applied to the working frame; unparseable dates excluded by range comparisons. Facets return distinct values (trimmed, non-empty) for filter controls. Non-fatal warnings when filters match 0 rows or a column is missing.

### KPIs & Aggregations
Revenue/orders/AOV/profit/margin/quantity computed from numeric sums; order count falls back to row count if no order ID. Calculation notes explain methodology (e.g., distinct order IDs, ignoring non-numeric cells). Data quality includes per-column missing %, empty columns, duplicate rows.

### Charts
Plotly figures built via `go.Figure`, styled with shared layout (`Manrope` font, white template, consistent axes/hover). Each builder returns `(fig, reason)` or `(None, reason)` on insufficient data; serialization uses `fig.to_json()` (JSON-safe). Cache key: `(dataset_id, (rows, filesize, mtime_ns), sorted(params))`, TTL via `CHART_CACHE_TTL_SECONDS` (default 60s), max 64 entries, thread-safe.

### Forecasting
- Monthly aggregation: `pd.to_period("M")`, sum sales per month, drop rows with unparseable date/sales.
- Holdout: if `months >= MIN_MONTHS_FOR_EVALUATION (6)`, test = `min(3, max(1, months//4))` months (chronological tail), train = rest. Baseline = last training value repeated. Metrics via `sklearn.metrics.mean_absolute_error`/`mean_squared_error`; MAPE only where actual != 0.
- Model trained on full history for future forecasts (periods 1..12). `raw_prediction < 0` → `predicted_sales = 0`, warning emitted. Returns honest comparison (model may be worse than baseline) and explanatory notes/warnings.

### Frontend
- `lib/api.ts`: typed client, `ApiError`, `buildUrl`, XHR `uploadWithProgress` (progress %), exposes `api.*` methods matching endpoints.
- `components/PlotlyChart.tsx`: dynamic `import('plotly.js-dist')` with CJS/ESM-safe resolution, `Plotly.react`, `Plotly.purge` on unmount, `ResizeObserver` for resize, config disables logo/modebar.
- `components/ui.tsx`: presentational primitives (KPI cards with optional sparkline, states, warnings, selects/fields, chips, metric cards, chart panel).
- Views: `OverviewView` (KPIs + 4 charts + quick links), `DatasetsView` (upload + list + preview + profile), `AnalyticsView` (column mapping + filters + facets + all 6 charts + KPI strip), `ForecastView` (setup + evaluation metrics + figure + forecast table), `ReportsView` (summary tables + method notes + CSV export of preview + print).
- `app/page.tsx`: app shell (sidebar/topbar/heading/notice/modal), dataset selection state, live API status, export of selected dataset preview CSV, upload modal with progress.
- `lib/useAsync.ts`: loader with deps + nonce + cancel guard. `lib/csv.ts`: CSV escaping + download helper.

## 5) Data Format Expectations

The bundled/sample and uploaded datasets work best with common sales columns. Detection looks for (case-insensitive/fuzzy):  
Date: `date, order date, invoice date, purchase date, created at, timestamp, month, period`  
Revenue/Sales: `revenue, sales, total sales, net sales, amount, total amount, price, turnover, total`  
Order ID: `order id, orderid, transaction id, invoice no, order number`  
Category: `category, product category, sub category, segment, department, product line, product group`  
Region: `region, country, state, market, territory, zone, province, area, location, city`  
Product: `product, product name, item, sku, model, description`  
Profit: `profit, net profit, gross profit, margin, profit margin, income, earnings`  
Quantity: `quantity, qty, units, units sold, volume, count`  
Cost: `cost, total cost, cogs, unit cost` (not required but recognized)

Constraints: CSV/XLSX, ≤20MB, ≤1M rows, ≤500 columns, unique non-empty column names, non-empty files. Dates parsed via `pd.to_datetime` (errors→coerce). Numerics parsed via `pd.to_numeric`.

## 6) Usage Guide (Quick Start)

1. **Backend**: set `MONGODB_URL` in `backend/.env`, activate venv, `uvicorn app.main:app --port 8000`.
2. **Frontend**: set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` in `frontend/ml-bi-platform/.env.local`, `npm run dev`.
3. **Load data**: in UI → Import data → Upload CSV/XLSX or "Use sample data" (calls `POST /datasets/sample`). Select dataset.
4. **Explore**: Overview shows KPIs + charts. Analytics allows column mapping + filters + all charts. Reports exports CSV of preview + printable summary.
5. **Forecast**: ML predictions → select date/sales columns + horizon → Run forecast. Review honest evaluation, warnings (including clamping), and forecast table/figure.

## 7) Testing & Verification

- Backend unit/integration: `pytest -q` → 80 passed (covers analytics, charts, forecasting, datasets API, integration flows). Fixtures in `backend/tests/conftest.py` (`sample_frame`, `sales_frame`, `messy_frame`, `no_date_frame`).
- Frontend: `npx tsc --noEmit` (type-safe), `npm run build` (production build passes). Plotly dynamically imported; no SSR of heavy bundles required.
- Live smoke (verified): sample load 153 rows, overview KPIs correct, charts 5 ready + 1 unavailable (no missing values), forecast evaluated with honest baseline comparison.

## 8) Notes & Limitations

- CORS allows `http://localhost:3000,http://127.0.0.1:3000` by default (configurable).
- In-process chart cache (TTL-based) per dataset signature + params; not distributed.
- Forecasting uses linear trend (captures trend, not seasonality). Honest baseline comparison is shown; warnings surfaced when model underperforms.
- MAPE excluded on zero actuals to avoid division by zero.
- No DELETE endpoints (destructive operations intentionally not exposed).
- Stubs: `assistant.py`, `predictions.py`, `reports.py` exist but are not wired into routers.

## 9) Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `/health/database` returns 503 | MongoDB unreachable | Check `MONGODB_URL`, Atlas IP allowlist, credentials, network. |
| CSV won't parse | Encoding/line breaks | Upload reads utf-8-sig/utf-8/cp1252; ensure valid CSV. |
| Charts show "unavailable" | Missing/undetected columns or insufficient data | Use Analytics → Column mapping to set explicit columns; check filters. |
| Forecast: "insufficient_data" | < 6 months history | Need ≥6 months for holdout evaluation (≥3 for forecast). Add more history. |
| Negative forecasts clamped | Linear trend extrapolates below 0 | Warning shown; treat as non-actionable unless history supports; consider different horizon/model. |
| Frontend can't reach API | Wrong base URL/CORS | Set `NEXT_PUBLIC_API_BASE_URL` to `http://localhost:8000/api/v1`; ensure backend CORS includes frontend origin. |
| Plotly doesn't render | Dynamic import blocked | Check network; component falls back to error state if bundle fails to load. |

## License

Proprietary/demo project as-is. Do not commit secrets (`.env`, credentials).#   M L _ B u s i n e s s _ I n t e l l i g e n c e _ P l a t o f o r m  
 