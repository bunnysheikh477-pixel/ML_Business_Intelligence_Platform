# Northstar BI — ML Business Intelligence Frontend

A polished, responsive Next.js + TypeScript + Tailwind CSS dashboard concept with a dark sidebar and light analytics workspace.

## Included
- Responsive sidebar navigation and mobile drawer
- KPI cards with sparkline accents
- Interactive revenue/profit area chart, product mix donut, and regional bar chart (Recharts)
- Region and product filters, plus date-range UI
- CSV upload with browser-side parsing and dataset preview/search
- CSV export of the built-in sales dataset with selected filters
- Dedicated ML predictions view (demo-only forecast state)
- No backend or API key required to run the UI

## Requirements
- Node.js 20.9+ recommended
- npm

## Run locally

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Notes before production
- The dashboard starts with fictional sample sales data.
- Uploaded CSV files are parsed locally in the browser and shown in the dataset preview. KPI charts intentionally remain on the sample sales schema until you map the uploaded column names and values to your backend data contract.
- The forecast values are illustrative. Connect the `Run prediction` action to your FastAPI model endpoint before using for decisions.
- Connect upload, auth, datasets, and analytics to FastAPI; store secrets server-side. Never expose Gemini API keys in client-side code.
