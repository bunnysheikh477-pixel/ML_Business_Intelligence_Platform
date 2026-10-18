'use client';

import {
  Activity,
  BriefcaseBusiness,
  Database,
  Layers,
  ShoppingBag,
  Target,
  TrendingUp,
} from 'lucide-react';

import { api, type ChartsResponse, type Dataset, type AnalyticsOverview } from '@/lib/api';
import { useAsync } from '@/lib/useAsync';
import ChartCard from '@/components/ChartCard';
import {
  KpiCard,
  MetricCard,
  RefreshButton,
  StateBlock,
  WarningList,
  formatCompact,
  formatNumber,
} from '@/components/ui';

type OverviewPayload = {
  overview: AnalyticsOverview | null;
  charts: ChartsResponse | null;
};

export default function OverviewView({
  datasets,
  selectedId,
  onSelect,
  onRequestUpload,
  onOpenAnalytics,
  onLoadSample,
  loadingSample,
}: {
  datasets: Dataset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRequestUpload: () => void;
  onOpenAnalytics: () => void;
  onLoadSample: () => void;
  loadingSample: boolean;
}) {
  const { data, error, loading, reload } = useAsync<OverviewPayload>(
    async () => {
      if (!selectedId) return { overview: null, charts: null };

      const [overview, charts] = await Promise.all([
        api.getOverview(selectedId),
        api.getCharts(selectedId),
      ]);

      return { overview, charts };
    },
    [selectedId],
  );

  const overview = data?.overview ?? null;
  const charts = data?.charts ?? null;
  const kpis = overview?.kpis ?? null;

  const monthlyRevenue = overview?.monthly_revenue ?? [];
  const spark = monthlyRevenue.map((row) => row.revenue);
  const chartByKey = (key: string) =>
    (charts?.charts ?? []).find((chart) => chart.key === key);

  const toolbar = (
    <div className="view-toolbar">
      <span className="toolbar-label">
        <Database size={14} /> Dataset
      </span>
      <label className="filter-select">
        <select
          value={selectedId ?? ''}
          onChange={(event) => onSelect(event.target.value)}
          aria-label="Select dataset"
          disabled={!datasets.length}
        >
          <option value="">
            {datasets.length ? 'Select a dataset' : 'No datasets available'}
          </option>
          {datasets.map((dataset) => (
            <option key={dataset.id} value={dataset.id}>
              {dataset.name} · {dataset.row_count} rows
            </option>
          ))}
        </select>
      </label>
      <button type="button" className="button button-secondary button-small" onClick={onRequestUpload}>
        <Layers size={14} /> Add data
      </button>
      <div className="toolbar-spacer" />
      <span className="updated-label">
        <span /> {charts ? (charts.cached ? 'Served from chart cache' : 'Freshly generated') : 'Idle'}
      </span>
      <RefreshButton onClick={reload} disabled={loading || !selectedId} />
    </div>
  );

  if (!datasets.length) {
    return (
      <div className="panel view-panel">
        <StateBlock
          kind="empty"
          title="No datasets yet"
          message="Upload a CSV or XLSX file, or load the bundled sample dataset to explore the platform."
          action={
            <div className="heading-actions">
              <button type="button" className="button button-primary" onClick={onRequestUpload}>
                <Database size={15} /> Upload a dataset
              </button>
              <button
                type="button"
                className="button button-secondary"
                onClick={onLoadSample}
                disabled={loadingSample}
              >
                <Layers size={15} /> {loadingSample ? 'Loading…' : 'Load sample dataset'}
              </button>
            </div>
          }
        />
      </div>
    );
  }

  return (
    <>
      {toolbar}

      {!selectedId ? (
        <div className="panel view-panel">
          <StateBlock
            kind="empty"
            title="Select a dataset"
            message="Choose a dataset above to load its KPIs and Python-generated charts."
          />
        </div>
      ) : loading ? (
        <div className="panel view-panel">
          <StateBlock kind="loading" title="Calculating KPIs and charts" message="Running aggregations in Python…" />
        </div>
      ) : error ? (
        <div className="panel view-panel">
          <StateBlock
            kind="error"
            title="Could not load this dataset"
            message={error}
            action={<RefreshButton onClick={reload} label="Try again" />}
          />
        </div>
      ) : (
        <>
          <WarningList warnings={charts?.warnings ?? []} />

          <section className="kpi-grid">
            <KpiCard
              label="Total revenue"
              value={formatNumber(kpis?.total_revenue, 2)}
              hint={
                kpis?.revenue_column
                  ? `Sum of '${kpis.revenue_column}'`
                  : 'No revenue column detected'
              }
              icon={<BriefcaseBusiness size={18} />}
              tone="violet"
              spark={spark}
            />
            <KpiCard
              label="Total profit"
              value={formatNumber(kpis?.total_profit, 2)}
              hint={
                kpis?.profit_margin_percent !== null && kpis?.profit_margin_percent !== undefined
                  ? `Margin ${formatNumber(kpis.profit_margin_percent, 2)}%`
                  : 'No profit column detected'
              }
              icon={<TrendingUp size={18} />}
              tone="mint"
            />
            <KpiCard
              label="Total orders"
              value={formatNumber(kpis?.total_orders)}
              hint={
                kpis?.orders_count_method === 'distinct_order_id'
                  ? `Distinct '${kpis.order_id_column}' values`
                  : 'Row count (no order ID column)'
              }
              icon={<ShoppingBag size={18} />}
              tone="amber"
            />
            <KpiCard
              label="Average order value"
              value={formatNumber(kpis?.average_order_value, 2)}
              hint="Revenue ÷ orders"
              icon={<Target size={18} />}
              tone="rose"
            />
          </section>

          <section className="metrics-grid">
            <MetricCard label="Rows analysed" value={formatNumber(overview?.rows_analyzed)} hint={`${formatNumber(kpis?.total_columns)} columns`} />
            <MetricCard
              label="Quantity sold"
              value={formatNumber(kpis?.total_quantity, 2)}
              hint={kpis?.quantity_column ? `Sum of '${kpis.quantity_column}'` : 'No quantity column'}
            />
            <MetricCard
              label="Missing cells"
              value={`${formatNumber(kpis?.data_quality.missing_percentage, 2)}%`}
              hint={`${formatNumber(kpis?.data_quality.missing_cells)} of ${formatNumber(kpis?.data_quality.total_cells)} cells`}
            />
            <MetricCard
              label="Duplicate rows"
              value={formatNumber(kpis?.data_quality.duplicate_rows)}
              hint={`${formatNumber(kpis?.data_quality.columns_missing_count)} columns with gaps`}
            />
          </section>

          <section className="charts-matrix charts-matrix-wide mt-15">
            {chartByKey('monthly_revenue') ? (
              <ChartCard
                chart={chartByKey('monthly_revenue')!}
                kicker="REVENUE PERFORMANCE"
                tone="violet"
                height={340}
              />
            ) : null}
            {chartByKey('sales_by_region') ? (
              <ChartCard
                chart={chartByKey('sales_by_region')!}
                kicker="REGIONAL PERFORMANCE"
                tone="amber"
                height={340}
              />
            ) : null}
          </section>

          <section className="charts-matrix mt-15">
            {chartByKey('sales_by_category') ? (
              <ChartCard
                chart={chartByKey('sales_by_category')!}
                kicker="REVENUE BREAKDOWN"
                tone="mint"
                height={320}
              />
            ) : null}
            {chartByKey('top_products') ? (
              <ChartCard
                chart={chartByKey('top_products')!}
                kicker="PRODUCT PERFORMANCE"
                tone="rose"
                height={320}
              />
            ) : null}
          </section>

          <section className="panel view-panel mt-15">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">
                  <span className="mini-dot violet-dot" /> NEXT STEP
                </div>
                <h2>Go deeper</h2>
                <p className="panel-description">
                  Filter by date, category and region, and inspect the raw rows behind these metrics.
                </p>
              </div>
              <button type="button" className="button button-primary button-small" onClick={onOpenAnalytics}>
                <Activity size={15} /> Open analytics
              </button>
            </div>
            <div className="metrics-grid mt-15">
              <MetricCard label="Months in range" value={formatNumber(monthlyRevenue.length)} hint={monthlyRevenue.length ? `${monthlyRevenue[0].month} → ${monthlyRevenue[monthlyRevenue.length - 1].month}` : 'No monthly data'} />
              <MetricCard label="Top region" value={overview?.region_sales?.[0]?.region ?? '—'} hint={overview?.region_sales?.[0] ? `${formatCompact(overview.region_sales[0].revenue)} revenue` : 'Not available'} />
              <MetricCard label="Top category" value={overview?.category_sales?.[0]?.category ?? '—'} hint={overview?.category_sales?.[0] ? `${formatCompact(overview.category_sales[0].revenue)} revenue` : 'Not available'} />
              <MetricCard label="Top product" value={overview?.top_products?.[0]?.product ?? '—'} hint={overview?.top_products?.[0] ? `${formatCompact(overview.top_products[0].revenue)} revenue` : 'Not available'} />
            </div>
          </section>
        </>
      )}
    </>
  );
}
