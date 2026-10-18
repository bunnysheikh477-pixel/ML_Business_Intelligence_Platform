'use client';

import { useEffect, useState } from 'react';
import {
  CalendarRange,
  Filter,
  RotateCcw,
  SlidersHorizontal,
} from 'lucide-react';

import {
  api,
  type AnalysisFilters,
  type AnalyticsOverview,
  type ChartsResponse,
  type ColumnMapping,
  type Dataset,
} from '@/lib/api';
import { useAsync } from '@/lib/useAsync';
import ChartCard from '@/components/ChartCard';
import {
  Chip,
  FieldSelect,
  KpiCard,
  MetricCard,
  RefreshButton,
  StateBlock,
  TextField,
  WarningList,
  formatNumber,
} from '@/components/ui';

type MappingState = {
  mapping: ColumnMapping;
  filters: AnalysisFilters;
};

function detectedMapping(detected: Record<string, string | null>): ColumnMapping {
  return {
    date_column: detected.date ?? null,
    sales_column: detected.revenue ?? null,
    category_column: detected.category ?? null,
    region_column: detected.region ?? null,
    profit_column: detected.profit ?? null,
    product_column: detected.product ?? null,
    quantity_column: detected.quantity ?? null,
  };
}

const CHART_TONES: Record<string, 'violet' | 'mint' | 'amber' | 'rose'> = {
  monthly_revenue: 'violet',
  sales_by_category: 'mint',
  sales_by_region: 'amber',
  top_products: 'rose',
  profit_vs_revenue: 'mint',
  missing_values: 'amber',
};

export default function AnalyticsView({
  datasets,
  selectedId,
  onSelect,
}: {
  datasets: Dataset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [draft, setDraft] = useState<MappingState>({ mapping: {}, filters: {} });
  const [applied, setApplied] = useState<MappingState>({ mapping: {}, filters: {} });
  const [scope, setScope] = useState<string | null>(null);

  const details = useAsync(
    async () => {
      if (!selectedId) return null;
      const response = await api.getDatasetDetails(selectedId);
      return response.dataset;
    },
    [selectedId],
  );

  useEffect(() => {
    if (!details.data || scope === details.data.id) return;

    const initial: MappingState = {
      mapping: detectedMapping(details.data.detected_columns),
      filters: {},
    };

    setScope(details.data.id);
    setDraft(initial);
    setApplied(initial);
  }, [details.data, scope]);

  const appliedKey = JSON.stringify(applied);

  const report = useAsync<{ overview: AnalyticsOverview; charts: ChartsResponse } | null>(
    async () => {
      if (!selectedId) return null;

      const [overview, charts] = await Promise.all([
        api.getOverview(selectedId, applied.mapping, applied.filters),
        api.getCharts(selectedId, applied.mapping, applied.filters),
      ]);

      return { overview, charts };
    },
    [selectedId, appliedKey],
  );

  const availableColumns =
    details.data?.columns ?? report.data?.overview.available_columns ?? [];
  const facets = report.data?.overview.facets ?? { category: [], region: [] };
  const filters = applied.filters;

  function clearFilter(key: keyof AnalysisFilters) {
    const nextApplied = { ...applied, filters: { ...applied.filters, [key]: null } };
    setApplied(nextApplied);
    setDraft({ ...draft, filters: { ...draft.filters, [key]: null } });
  }

  const activeChips: { label: string; key: keyof AnalysisFilters }[] = [];
  if (filters.date_from) activeChips.push({ label: `From ${filters.date_from}`, key: 'date_from' });
  if (filters.date_to) activeChips.push({ label: `To ${filters.date_to}`, key: 'date_to' });
  if (filters.category_value) activeChips.push({ label: `Category: ${filters.category_value}`, key: 'category_value' });
  if (filters.region_value) activeChips.push({ label: `Region: ${filters.region_value}`, key: 'region_value' });

  if (!datasets.length) {
    return (
      <div className="panel view-panel">
        <StateBlock
          kind="empty"
          title="No datasets available"
          message="Upload data or load the sample dataset before running analytics."
        />
      </div>
    );
  }

  return (
    <>
      <div className="view-toolbar">
        <span className="toolbar-label">
          <CalendarRange size={14} /> Dataset
        </span>
        <label className="filter-select">
          <select
            value={selectedId ?? ''}
            onChange={(event) => onSelect(event.target.value)}
            aria-label="Select dataset"
          >
            <option value="">Select a dataset</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name} · {dataset.row_count} rows
              </option>
            ))}
          </select>
        </label>
        <div className="toolbar-spacer" />
        <RefreshButton onClick={report.reload} disabled={report.loading || !selectedId} />
      </div>

      {!selectedId ? (
        <div className="panel view-panel">
          <StateBlock kind="empty" title="Select a dataset" message="Choose a dataset to filter and analyse." />
        </div>
      ) : (
        <>
          <section className="panel view-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">
                  <span className="mini-dot violet-dot" /> <Filter size={11} /> FILTERS
                </div>
                <h2>Refine the analysis</h2>
                <p className="panel-description">
                  Filters are applied on the backend over the raw rows using the mapped columns.
                </p>
              </div>
              <span className="record-count">
                {formatNumber(report.data?.overview.rows_analyzed)} rows in scope
              </span>
            </div>

            <div className="view-toolbar filter-bar mt-15">
              <TextField
                label="From date"
                type="date"
                value={draft.filters.date_from ?? ''}
                onChange={(value) => setDraft({ ...draft, filters: { ...draft.filters, date_from: value } })}
              />
              <TextField
                label="To date"
                type="date"
                value={draft.filters.date_to ?? ''}
                onChange={(value) => setDraft({ ...draft, filters: { ...draft.filters, date_to: value } })}
              />
              <FieldSelect
                label="Category"
                value={draft.filters.category_value ?? ''}
                onChange={(value) => setDraft({ ...draft, filters: { ...draft.filters, category_value: value } })}
                options={facets.category.map((value) => ({ value, label: value }))}
                placeholder="All categories"
              />
              <FieldSelect
                label="Region"
                value={draft.filters.region_value ?? ''}
                onChange={(value) => setDraft({ ...draft, filters: { ...draft.filters, region_value: value } })}
                options={facets.region.map((value) => ({ value, label: value }))}
                placeholder="All regions"
              />
              <div className="toolbar-spacer" />
              <button
                type="button"
                className="button button-primary button-small"
                onClick={() => setApplied(draft)}
                disabled={report.loading}
              >
                <SlidersHorizontal size={14} /> Apply filters
              </button>
              <button
                type="button"
                className="button button-secondary button-small"
                onClick={() => {
                  const reset: MappingState = {
                    mapping: detectedMapping(details.data?.detected_columns ?? {}),
                    filters: {},
                  };
                  setDraft(reset);
                  setApplied(reset);
                }}
              >
                <RotateCcw size={14} /> Reset
              </button>
            </div>

            {activeChips.length ? (
              <div className="chip-row">
                {activeChips.map((chip) => (
                  <Chip key={chip.key} onClear={() => clearFilter(chip.key)}>
                    {chip.label}
                  </Chip>
                ))}
              </div>
            ) : (
              <p className="panel-description">No filters applied — analysing the full dataset.</p>
            )}

            {details.data ? (
              <details className="mapping-panel">
                <summary>
                  <SlidersHorizontal size={13} /> Column mapping
                  <span>
                    {Object.entries(details.data.detected_columns)
                      .filter(([, value]) => value)
                      .map(([role, value]) => `${role} → ${value}`)
                      .join(' · ') || 'No columns detected'}
                  </span>
                </summary>
                <div className="mapping-grid">
                  <FieldSelect
                    label="Date column"
                    value={draft.mapping.date_column ?? ''}
                    onChange={(value) => setDraft({ ...draft, mapping: { ...draft.mapping, date_column: value } })}
                    options={availableColumns.map((value) => ({ value, label: value }))}
                    placeholder="Not detected"
                  />
                  <FieldSelect
                    label="Sales column"
                    value={draft.mapping.sales_column ?? ''}
                    onChange={(value) => setDraft({ ...draft, mapping: { ...draft.mapping, sales_column: value } })}
                    options={availableColumns.map((value) => ({ value, label: value }))}
                    placeholder="Not detected"
                  />
                  <FieldSelect
                    label="Category column"
                    value={draft.mapping.category_column ?? ''}
                    onChange={(value) => setDraft({ ...draft, mapping: { ...draft.mapping, category_column: value } })}
                    options={availableColumns.map((value) => ({ value, label: value }))}
                    placeholder="Not detected"
                  />
                  <FieldSelect
                    label="Region column"
                    value={draft.mapping.region_column ?? ''}
                    onChange={(value) => setDraft({ ...draft, mapping: { ...draft.mapping, region_column: value } })}
                    options={availableColumns.map((value) => ({ value, label: value }))}
                    placeholder="Not detected"
                  />
                  <FieldSelect
                    label="Profit column"
                    value={draft.mapping.profit_column ?? ''}
                    onChange={(value) => setDraft({ ...draft, mapping: { ...draft.mapping, profit_column: value } })}
                    options={availableColumns.map((value) => ({ value, label: value }))}
                    placeholder="Not detected"
                  />
                  <FieldSelect
                    label="Product column"
                    value={draft.mapping.product_column ?? ''}
                    onChange={(value) => setDraft({ ...draft, mapping: { ...draft.mapping, product_column: value } })}
                    options={availableColumns.map((value) => ({ value, label: value }))}
                    placeholder="Not detected"
                  />
                  <FieldSelect
                    label="Quantity column"
                    value={draft.mapping.quantity_column ?? ''}
                    onChange={(value) => setDraft({ ...draft, mapping: { ...draft.mapping, quantity_column: value } })}
                    options={availableColumns.map((value) => ({ value, label: value }))}
                    placeholder="Not detected"
                  />
                  <button
                    type="button"
                    className="button button-primary button-small"
                    onClick={() => setApplied(draft)}
                  >
                    <SlidersHorizontal size={14} /> Apply mapping
                  </button>
                </div>
              </details>
            ) : null}
          </section>

          {report.loading ? (
            <div className="panel view-panel">
              <StateBlock kind="loading" title="Running analytics" message="Aggregating rows and generating charts…" />
            </div>
          ) : report.error ? (
            <div className="panel view-panel">
              <StateBlock
                kind="error"
                title="Analytics failed"
                message={report.error}
                action={
                  <button type="button" className="button button-secondary button-small" onClick={report.reload}>
                    Try again
                  </button>
                }
              />
            </div>
          ) : report.data ? (
            <>
              <WarningList warnings={report.data.overview.warnings} />

              <section className="kpi-grid">
                <KpiCard
                  label="Revenue in scope"
                  value={formatNumber(report.data.overview.kpis.total_revenue, 2)}
                  hint={`${formatNumber(report.data.overview.rows_analyzed)} rows analysed`}
                  icon={<CalendarRange size={18} />}
                  tone="violet"
                />
                <KpiCard
                  label="Profit in scope"
                  value={formatNumber(report.data.overview.kpis.total_profit, 2)}
                  hint={
                    report.data.overview.kpis.profit_margin_percent !== null
                      ? `Margin ${formatNumber(report.data.overview.kpis.profit_margin_percent, 2)}%`
                      : 'No profit column'
                  }
                  icon={<Filter size={18} />}
                  tone="mint"
                />
                <KpiCard
                  label="Orders"
                  value={formatNumber(report.data.overview.kpis.total_orders)}
                  hint={report.data.overview.kpis.orders_count_method}
                  icon={<SlidersHorizontal size={18} />}
                  tone="amber"
                />
                <KpiCard
                  label="Average order value"
                  value={formatNumber(report.data.overview.kpis.average_order_value, 2)}
                  hint="Revenue ÷ orders"
                  icon={<RotateCcw size={18} />}
                  tone="rose"
                />
              </section>

              <section className="metrics-grid">
                <MetricCard label="Months" value={formatNumber(report.data.overview.monthly_revenue.length)} hint="Monthly buckets with data" />
                <MetricCard label="Categories" value={formatNumber(report.data.overview.category_sales.length)} hint="Distinct categories in scope" />
                <MetricCard label="Regions" value={formatNumber(report.data.overview.region_sales.length)} hint="Distinct regions in scope" />
                <MetricCard
                  label="Missing cells"
                  value={`${formatNumber(report.data.overview.kpis.data_quality.missing_percentage, 2)}%`}
                  hint="Across the analysed dataset"
                />
              </section>

              <section className="charts-matrix charts-matrix-wide mt-15">
                {report.data.charts.charts.map((chart) => (
                  <ChartCard
                    key={chart.key}
                    chart={chart}
                    tone={CHART_TONES[chart.key] ?? 'violet'}
                    height={chart.key === 'monthly_revenue' ? 340 : 320}
                  />
                ))}
              </section>
            </>
          ) : null}
        </>
      )}
    </>
  );
}
