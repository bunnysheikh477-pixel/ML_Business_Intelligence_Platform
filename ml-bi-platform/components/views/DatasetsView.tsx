'use client';

import { useMemo, useState } from 'react';
import {
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Search,
  Sparkles,
  Table2,
} from 'lucide-react';

import {
  api,
  type Dataset,
  type DatasetDetails,
  type DatasetPreview,
} from '@/lib/api';
import { useAsync } from '@/lib/useAsync';
import UploadForm from '@/components/UploadForm';
import {
  MetricCard,
  RefreshButton,
  StateBlock,
  formatDateTime,
  formatNumber,
} from '@/components/ui';

const PREVIEW_LIMITS = [10, 25, 50, 100];

export default function DatasetsView({
  datasets,
  selectedId,
  onSelect,
  loading,
  error,
  onReload,
  onUploaded,
  onLoadSample,
  loadingSample,
}: {
  datasets: Dataset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loading: boolean;
  error: string;
  onReload: () => void;
  onUploaded: (dataset: Dataset) => void;
  onLoadSample: () => void;
  loadingSample: boolean;
}) {
  const [previewLimit, setPreviewLimit] = useState(25);
  const [search, setSearch] = useState('');

  const details = useAsync<DatasetDetails | null>(
    async () => {
      if (!selectedId) return null;
      const response = await api.getDatasetDetails(selectedId);
      return response.dataset;
    },
    [selectedId],
  );

  const preview = useAsync<DatasetPreview | null>(
    async () => {
      if (!selectedId) return null;
      const response = await api.getDatasetPreview(selectedId, previewLimit);
      return response.data;
    },
    [selectedId, previewLimit],
  );

  const rows = preview.data?.rows ?? [];
  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return rows;

    return rows.filter((row) =>
      Object.values(row).some((value) =>
        String(value ?? '').toLowerCase().includes(term),
      ),
    );
  }, [rows, search]);

  const profile = details.data?.profile;

  return (
    <>
      <section className="panel view-panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">
              <span className="mini-dot violet-dot" /> SYNC STATUS
            </div>
            <h2>Dataset inventory</h2>
            <p className="panel-description">
              Every dataset below is stored on the backend with metadata in MongoDB.
            </p>
          </div>
          <RefreshButton onClick={onReload} disabled={loading} label="Reload" />
        </div>
        <div className="metrics-grid mt-15">
          <MetricCard label="Datasets" value={formatNumber(datasets.length)} hint="Available for analysis" />
          <MetricCard
            label="Total rows"
            value={formatNumber(datasets.reduce((total, item) => total + item.row_count, 0))}
            hint="Across all datasets"
          />
          <MetricCard
            label="Columns"
            value={formatNumber(
              datasets.reduce((total, item) => total + item.column_count, 0),
            )}
            hint="Summed across datasets"
          />
          <MetricCard
            label="Selected"
            value={datasets.find((item) => item.id === selectedId)?.name ?? '—'}
            hint={
              selectedId
                ? `Updated ${formatDateTime(
                    datasets.find((item) => item.id === selectedId)?.created_at,
                  )}`
                : 'Pick a dataset below'
            }
          />
        </div>
      </section>

      <section className="panel view-panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">
              <span className="mini-dot mint-dot" /> DATASET ADMINISTRATION
            </div>
            <h2>Upload dataset</h2>
            <p className="panel-description">
              CSV or XLSX files are parsed, validated and profiled before storage.
            </p>
          </div>
          <button
            type="button"
            className="button button-secondary button-small"
            onClick={onLoadSample}
            disabled={loadingSample}
          >
            <Sparkles size={14} /> {loadingSample ? 'Loading…' : 'Load sample dataset'}
          </button>
        </div>
        <div className="mt-15">
          <UploadForm onUploaded={onUploaded} />
        </div>
      </section>

      <section className="panel view-panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">
              <span className="mini-dot amber-dot" /> CONNECTED SOURCES
            </div>
            <h2>Datasets</h2>
            <p className="panel-description">
              Select a dataset to preview rows and inspect the column profile.
            </p>
          </div>
          <span className="record-count">{formatNumber(datasets.length)} total</span>
        </div>

        {loading ? (
          <StateBlock kind="loading" title="Loading datasets" message="Contacting the backend…" />
        ) : error ? (
          <StateBlock
            kind="error"
            title="Could not load datasets"
            message={error}
            action={<RefreshButton onClick={onReload} label="Try again" />}
          />
        ) : datasets.length ? (
          <div className="mt-15">
            {datasets.map((dataset) => {
              const active = dataset.id === selectedId;

              return (
                <button
                  type="button"
                  key={dataset.id}
                  className={`dataset-row ${active ? 'selected' : ''}`}
                  onClick={() => onSelect(dataset.id)}
                  aria-pressed={active}
                >
                  <span className="file-meta-icon">
                    <FileSpreadsheet size={16} />
                  </span>
                  <span className="dataset-row-copy">
                    <strong>{dataset.name}</strong>
                    <span>
                      {formatNumber(dataset.row_count)} rows · {formatNumber(dataset.column_count)}{' '}
                      columns · {dataset.file_type.toUpperCase()} ·{' '}
                      {formatDateTime(dataset.created_at)}
                    </span>
                  </span>
                  {active ? (
                    <span className="chip">
                      <CheckCircle2 size={12} /> Selected
                    </span>
                  ) : (
                    <span className="view-all">Use this dataset</span>
                  )}
                </button>
              );
            })}
          </div>
        ) : (
          <StateBlock
            kind="empty"
            title="No datasets uploaded yet"
            message="Upload a CSV/XLSX file above, or load the bundled sample dataset."
            action={
              <button
                type="button"
                className="button button-primary"
                onClick={onLoadSample}
                disabled={loadingSample}
              >
                <Sparkles size={15} /> {loadingSample ? 'Loading…' : 'Load sample dataset'}
              </button>
            }
          />
        )}
      </section>

      {selectedId ? (
        <>
          <section className="panel view-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">
                  <span className="mini-dot violet-dot" /> <Database size={11} /> RAW ROWS
                </div>
                <h2>Preview · {details.data?.name ?? 'dataset'}</h2>
                <p className="panel-description">
                  First rows returned by the backend, filtered locally for convenience.
                </p>
              </div>
              <label className="filter-select">
                <select
                  value={String(previewLimit)}
                  onChange={(event) => setPreviewLimit(Number(event.target.value))}
                  aria-label="Preview row limit"
                >
                  {PREVIEW_LIMITS.map((limit) => (
                    <option key={limit} value={limit}>
                      Show {limit} rows
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="search-box mt-15">
              <Search size={14} />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Filter preview rows…"
                aria-label="Filter preview rows"
              />
            </label>

            {preview.loading ? (
              <StateBlock kind="loading" title="Loading rows" />
            ) : preview.error ? (
              <StateBlock
                kind="error"
                title="Could not load preview"
                message={preview.error}
                action={<RefreshButton onClick={preview.reload} label="Try again" />}
              />
            ) : !rows.length ? (
              <StateBlock kind="empty" title="No rows returned" message="The dataset is empty." />
            ) : !filtered.length ? (
              <div className="empty-search">No preview rows match “{search}”.</div>
            ) : (
              <div className="table-wrap mt-10">
                <table>
                  <thead>
                    <tr>
                      {(preview.data?.columns ?? []).map((column) => (
                        <th key={column}>{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((row, index) => (
                      <tr key={index}>
                        {(preview.data?.columns ?? []).map((column) => (
                          <td key={column}>
                            {row[column] === null || row[column] === undefined
                              ? '—'
                              : String(row[column])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="table-footer">
                  <span>
                    Showing {formatNumber(filtered.length)} of {formatNumber(rows.length)} fetched
                    rows
                  </span>
                  <span className="toolbar-spacer" />
                  <RefreshButton onClick={preview.reload} label="Reload rows" />
                </div>
              </div>
            )}
          </section>

          <section className="panel view-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">
                  <span className="mini-dot mint-dot" /> <Table2 size={11} /> COLUMN PROFILE
                </div>
                <h2>Data profile</h2>
                <p className="panel-description">
                  Dtypes, missing values and cardinality per column, computed in Python.
                </p>
              </div>
              <RefreshButton onClick={details.reload} disabled={details.loading} />
            </div>

            {details.loading ? (
              <StateBlock kind="loading" title="Profiling dataset" />
            ) : details.error ? (
              <StateBlock
                kind="error"
                title="Could not load the profile"
                message={details.error}
                action={<RefreshButton onClick={details.reload} label="Try again" />}
              />
            ) : (
              <>
                <div className="metrics-grid mt-15">
                  <MetricCard label="Rows" value={formatNumber(profile?.row_count)} />
                  <MetricCard label="Columns" value={formatNumber(profile?.column_count)} />
                  <MetricCard label="Duplicate rows" value={formatNumber(profile?.duplicate_rows)} />
                  <MetricCard
                    label="Empty columns"
                    value={formatNumber(
                      (profile?.columns ?? []).filter((column) => column.unique_values === 0).length,
                    )}
                  />
                </div>
                <div className="table-wrap mt-15">
                  <table>
                    <thead>
                      <tr>
                        <th>Column</th>
                        <th>Dtype</th>
                        <th>Missing</th>
                        <th>Missing %</th>
                        <th>Unique values</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(profile?.columns ?? []).map((column) => (
                        <tr key={column.name}>
                          <td className="product-cell">{column.name}</td>
                          <td>{column.dtype}</td>
                          <td>{formatNumber(column.missing_values)}</td>
                          <td>{formatNumber(column.missing_percentage, 2)}%</td>
                          <td>{formatNumber(column.unique_values)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        </>
      ) : null}
    </>
  );
}
