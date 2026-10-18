'use client';

import { useState } from 'react';
import { Download, FileText, Printer } from 'lucide-react';

import {
  api,
  type AnalyticsOverview,
  type Dataset,
  type DatasetPreview,
} from '@/lib/api';
import { useAsync } from '@/lib/useAsync';
import { downloadCsv, safeFilename } from '@/lib/csv';
import {
  MetricCard,
  RefreshButton,
  StateBlock,
  WarningList,
  formatDateTime,
  formatNumber,
} from '@/components/ui';

export default function ReportsView({
  datasets,
  selectedId,
  onSelect,
}: {
  datasets: Dataset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [exported, setExported] = useState('');

  const report = useAsync<{ overview: AnalyticsOverview; preview: DatasetPreview } | null>(
    async () => {
      if (!selectedId) return null;

      const [overview, preview] = await Promise.all([
        api.getOverview(selectedId),
        api.getDatasetPreview(selectedId, 100),
      ]);

      return { overview, preview: preview.data };
    },
    [selectedId],
  );

  function exportCsv() {
    if (!report.data) return;

    const { preview } = report.data;

    downloadCsv(
      safeFilename(preview.name, `preview-${preview.rows.length}-rows.csv`),
      preview.columns,
      preview.rows,
    );
    setExported(`Exported ${preview.rows.length} rows to CSV.`);
  }

  const selected = datasets.find((dataset) => dataset.id === selectedId) ?? null;
  const overview = report.data?.overview ?? null;
  const kpis = overview?.kpis ?? null;

  if (!datasets.length) {
    return (
      <div className="panel view-panel">
        <StateBlock
          kind="empty"
          title="Nothing to report"
          message="Upload a dataset or load the sample dataset to build a report."
        />
      </div>
    );
  }

  return (
    <>
      <div className="view-toolbar">
        <span className="toolbar-label">
          <FileText size={14} /> Report source
        </span>
        <label className="filter-select">
          <select
            value={selectedId ?? ''}
            onChange={(event) => onSelect(event.target.value)}
            aria-label="Select dataset for the report"
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
        <button
          type="button"
          className="button button-secondary button-small"
          onClick={exportCsv}
          disabled={!report.data}
        >
          <Download size={14} /> Export preview CSV
        </button>
        <button
          type="button"
          className="button button-primary button-small"
          onClick={() => window.print()}
        >
          <Printer size={14} /> Print / save as PDF
        </button>
        <RefreshButton onClick={report.reload} disabled={report.loading || !selectedId} />
      </div>

      {exported ? (
        <div className="notice">
          <span>{exported}</span>
          <button type="button" className="view-all" onClick={() => setExported('')}>
            Dismiss
          </button>
        </div>
      ) : null}

      {!selectedId ? (
        <div className="panel view-panel">
          <StateBlock kind="empty" title="Select a dataset" message="Choose a dataset to generate its report." />
        </div>
      ) : report.loading ? (
        <div className="panel view-panel">
          <StateBlock kind="loading" title="Compiling report" message="Recomputing KPIs from the raw rows…" />
        </div>
      ) : report.error ? (
        <div className="panel view-panel">
          <StateBlock
            kind="error"
            title="Could not build the report"
            message={report.error}
            action={<RefreshButton onClick={report.reload} label="Try again" />}
          />
        </div>
      ) : overview && kpis ? (
        <>
          <WarningList warnings={overview.warnings} />

          <section className="panel view-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">
                  <span className="mini-dot violet-dot" /> REPORT HEADER
                </div>
                <h2>{selected?.name ?? overview.dataset.name}</h2>
                <p className="panel-description">
                  {selected
                    ? `${formatNumber(selected.row_count)} rows · ${formatNumber(selected.column_count)} columns · ${selected.file_type.toUpperCase()} · imported ${formatDateTime(selected.created_at)}`
                    : overview.dataset.id}
                </p>
              </div>
            </div>
            <div className="metrics-grid mt-15">
              <MetricCard label="Rows analysed" value={formatNumber(overview.rows_analyzed)} hint={`${formatNumber(kpis.total_columns)} columns`} />
              <MetricCard label="Total revenue" value={formatNumber(kpis.total_revenue, 2)} hint={kpis.revenue_column ?? 'No revenue column'} />
              <MetricCard label="Total profit" value={formatNumber(kpis.total_profit, 2)} hint={kpis.profit_column ?? 'No profit column'} />
              <MetricCard
                label="Profit margin"
                value={
                  kpis.profit_margin_percent === null
                    ? '—'
                    : `${formatNumber(kpis.profit_margin_percent, 2)}%`
                }
                hint="Profit ÷ revenue"
              />
            </div>
          </section>

          <section className="panel view-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">
                  <span className="mini-dot mint-dot" /> KPI TABLE
                </div>
                <h2>Key metrics</h2>
                <p className="panel-description">Every metric below is computed on the backend from the stored rows.</p>
              </div>
            </div>
            <div className="table-wrap mt-15">
              <table>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Basis</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="product-cell">Total revenue</td>
                    <td>{formatNumber(kpis.total_revenue, 2)}</td>
                    <td>{kpis.revenue_column ?? 'Not available'}</td>
                  </tr>
                  <tr>
                    <td className="product-cell">Total orders</td>
                    <td>{formatNumber(kpis.total_orders)}</td>
                    <td>{kpis.orders_count_method}</td>
                  </tr>
                  <tr>
                    <td className="product-cell">Average order value</td>
                    <td>{formatNumber(kpis.average_order_value, 2)}</td>
                    <td>Revenue ÷ orders</td>
                  </tr>
                  <tr>
                    <td className="product-cell">Total profit</td>
                    <td>{formatNumber(kpis.total_profit, 2)}</td>
                    <td>{kpis.profit_column ?? 'Not available'}</td>
                  </tr>
                  <tr>
                    <td className="product-cell">Profit margin</td>
                    <td>
                      {kpis.profit_margin_percent === null
                        ? '—'
                        : `${formatNumber(kpis.profit_margin_percent, 2)}%`}
                    </td>
                    <td>Profit ÷ revenue × 100</td>
                  </tr>
                  <tr>
                    <td className="product-cell">Total quantity</td>
                    <td>{formatNumber(kpis.total_quantity, 2)}</td>
                    <td>{kpis.quantity_column ?? 'Not available'}</td>
                  </tr>
                  <tr>
                    <td className="product-cell">Missing cells</td>
                    <td>
                      {formatNumber(kpis.data_quality.missing_cells)} (
                      {formatNumber(kpis.data_quality.missing_percentage, 2)}%)
                    </td>
                    <td>
                      {formatNumber(kpis.data_quality.total_cells)} cells across{' '}
                      {formatNumber(kpis.data_quality.columns)} columns
                    </td>
                  </tr>
                  <tr>
                    <td className="product-cell">Duplicate rows</td>
                    <td>{formatNumber(kpis.data_quality.duplicate_rows)}</td>
                    <td>Full-row duplicates</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section className="charts-matrix mt-15">
            <div className="panel view-panel">
              <div className="panel-header">
                <div>
                  <div className="panel-kicker">
                    <span className="mini-dot amber-dot" /> TOP PERFORMERS
                  </div>
                  <h2>Products, categories and regions</h2>
                  <p className="panel-description">Ranked by revenue in the current dataset.</p>
                </div>
              </div>
              <div className="split-tables mt-15">
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Revenue</th>
                        <th>Share</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.top_products.slice(0, 6).map((row) => (
                        <tr key={row.product}>
                          <td className="product-cell">{row.product}</td>
                          <td>{formatNumber(row.revenue, 2)}</td>
                          <td>{formatNumber(row.share_percent, 2)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Category</th>
                        <th>Revenue</th>
                        <th>Share</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.category_sales.slice(0, 6).map((row) => (
                        <tr key={row.category}>
                          <td className="product-cell">{row.category}</td>
                          <td>{formatNumber(row.revenue, 2)}</td>
                          <td>{formatNumber(row.share_percent, 2)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="panel view-panel">
              <div className="panel-header">
                <div>
                  <div className="panel-kicker">
                    <span className="mini-dot rose-dot" /> METHOD NOTES
                  </div>
                  <h2>How these numbers were calculated</h2>
                  <p className="panel-description">Transparency notes returned by the analytics API.</p>
                </div>
              </div>
              <ul className="note-list">
                {kpis.calculation_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
              {kpis.data_quality.columns_with_missing.length ? (
                <>
                  <h3 className="subheading">Columns with missing values</h3>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Column</th>
                          <th>Missing</th>
                          <th>Missing %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {kpis.data_quality.columns_with_missing.map((column) => (
                          <tr key={column.name}>
                            <td className="product-cell">{column.name}</td>
                            <td>{formatNumber(column.missing_values)}</td>
                            <td>{formatNumber(column.missing_percentage, 2)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <p className="panel-description mt-10">
                  No missing values were found in the analysed dataset.
                </p>
              )}
            </div>
          </section>
        </>
      ) : null}
    </>
  );
}
