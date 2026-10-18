'use client';

import { useEffect, useState } from 'react';
import { BrainCircuit, Play, Target, TrendingUp } from 'lucide-react';

import {
  api,
  ApiError,
  type Dataset,
  type ForecastResponse,
} from '@/lib/api';
import { useAsync } from '@/lib/useAsync';
import PlotlyChart from '@/components/PlotlyChart';
import {
  ChartPanel,
  FieldSelect,
  KpiCard,
  MetricCard,
  RefreshButton,
  StateBlock,
  WarningList,
  formatNumber,
} from '@/components/ui';

const HORIZONS = [1, 2, 3, 4, 6, 9, 12];

export default function ForecastView({
  datasets,
  selectedId,
  onSelect,
}: {
  datasets: Dataset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [dateColumn, setDateColumn] = useState('');
  const [salesColumn, setSalesColumn] = useState('');
  const [periods, setPeriods] = useState('3');
  const [scope, setScope] = useState<string | null>(null);
  const [result, setResult] = useState<ForecastResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

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

    setScope(details.data.id);
    setDateColumn(details.data.detected_columns.date ?? '');
    setSalesColumn(details.data.detected_columns.revenue ?? '');
    setResult(null);
    setError('');
  }, [details.data, scope]);

  async function runForecast() {
    if (!selectedId) return;

    setRunning(true);
    setError('');

    try {
      const response = await api.runForecast(selectedId, {
        dateColumn: dateColumn || null,
        salesColumn: salesColumn || null,
        periods: Number(periods),
      });

      setResult(response);
    } catch (runError) {
      setResult(null);
      setError(
        runError instanceof ApiError
          ? runError.message
          : 'The forecast could not be generated for this dataset.',
      );
    } finally {
      setRunning(false);
    }
  }

  const evaluation = result?.data.evaluation;
  const availableColumns = details.data?.columns ?? [];

  if (!datasets.length) {
    return (
      <div className="panel view-panel">
        <StateBlock
          kind="empty"
          title="No datasets available"
          message="Upload a monthly sales dataset or load the sample dataset to train a forecast."
        />
      </div>
    );
  }

  return (
    <>
      <div className="view-toolbar">
        <span className="toolbar-label">
          <BrainCircuit size={14} /> Dataset
        </span>
        <label className="filter-select">
          <select
            value={selectedId ?? ''}
            onChange={(event) => onSelect(event.target.value)}
            aria-label="Select dataset for forecasting"
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
        <RefreshButton onClick={details.reload} disabled={details.loading || !selectedId} label="Reload columns" />
      </div>

      <section className="panel view-panel">
        <div className="panel-header">
          <div>
            <div className="panel-kicker">
              <span className="mini-dot violet-dot" /> <TrendingUp size={11} /> FORECAST SETUP
            </div>
            <h2>Sales forecasting</h2>
            <p className="panel-description">
              A linear trend model fitted in Python with a chronological hold-out and a naive
              last-value baseline, so the accuracy is measured honestly.
            </p>
          </div>
          <button
            type="button"
            className="button button-primary"
            onClick={runForecast}
            disabled={running || !selectedId || !dateColumn || !salesColumn}
          >
            <Play size={15} /> {running ? 'Training…' : 'Run forecast'}
          </button>
        </div>

        <div className="view-toolbar filter-bar mt-15">
          <FieldSelect
            label="Date column"
            value={dateColumn}
            onChange={setDateColumn}
            options={availableColumns.map((value) => ({ value, label: value }))}
            placeholder="Select a date column"
          />
          <FieldSelect
            label="Sales column"
            value={salesColumn}
            onChange={setSalesColumn}
            options={availableColumns.map((value) => ({ value, label: value }))}
            placeholder="Select a sales column"
          />
          <FieldSelect
            label="Forecast horizon"
            value={periods}
            onChange={setPeriods}
            options={HORIZONS.map((value) => ({
              value: String(value),
              label: `${value} month${value > 1 ? 's' : ''}`,
            }))}
            placeholder="3 months"
          />
        </div>

        {!dateColumn || !salesColumn ? (
          <WarningList
            warnings={[
              'Select both a date column and a sales column before running the forecast.',
            ]}
          />
        ) : null}

        {error ? (
          <StateBlock kind="error" title="Forecast failed" message={error} />
        ) : null}
      </section>

      {result ? (
        <>
          <WarningList warnings={result.data.warnings} />

          {evaluation && evaluation.status === 'insufficient_data' ? (
            <section className="panel view-panel">
              <StateBlock
                kind="empty"
                title="Not enough history to evaluate a forecast"
                message={evaluation.message}
              />
            </section>
          ) : evaluation && evaluation.status === 'evaluated' ? (
            <>
              <section className="kpi-grid">
                <KpiCard
                  label="Model MAE"
                  value={formatNumber(evaluation.model_metrics.mae, 2)}
                  hint={`${formatNumber(evaluation.train_months)} train / ${formatNumber(evaluation.test_months)} test months`}
                  icon={<BrainCircuit size={18} />}
                  tone="violet"
                />
                <KpiCard
                  label="Model RMSE"
                  value={formatNumber(evaluation.model_metrics.rmse, 2)}
                  hint={result.data.model}
                  icon={<TrendingUp size={18} />}
                  tone="mint"
                />
                <KpiCard
                  label="Baseline MAE"
                  value={formatNumber(evaluation.baseline.metrics.mae, 2)}
                  hint={evaluation.baseline.description}
                  icon={<Play size={18} />}
                  tone="amber"
                />
                <KpiCard
                  label="MAE change vs baseline"
                  value={
                    evaluation.comparison.mae_improvement_percent === null
                      ? '—'
                      : `${formatNumber(evaluation.comparison.mae_improvement_percent, 2)}%`
                  }
                  hint={
                    evaluation.comparison.model_better_than_baseline
                      ? 'Model beats the naive baseline'
                      : 'Baseline is more accurate'
                  }
                  icon={<Target size={18} />}
                  tone={evaluation.comparison.model_better_than_baseline ? 'mint' : 'rose'}
                />
              </section>

              <section className="metrics-grid">
                <MetricCard
                  label="MAPE"
                  value={
                    evaluation.model_metrics.mape_percent === null
                      ? 'n/a'
                      : `${formatNumber(evaluation.model_metrics.mape_percent, 2)}%`
                  }
                  hint="Only over non-zero actual months"
                />
                <MetricCard
                  label="History"
                  value={`${formatNumber(result.data.historical_months)} months`}
                  hint={`${result.data.history[0]?.month ?? '—'} → ${result.data.history[result.data.history.length - 1]?.month ?? '—'}`}
                />
                <MetricCard
                  label="Forecast horizon"
                  value={`${formatNumber(result.data.forecasts.length)} months`}
                  hint={result.data.forecasts[0] ? `Starts ${result.data.forecasts[0].month}` : 'No future periods'}
                />
                <MetricCard
                  label="Frequency"
                  value={result.data.frequency}
                  hint={`Target: ${result.data.target}`}
                />
              </section>

              <section className="panel view-panel mt-15">
                <div className="panel-header">
                  <div>
                    <div className="panel-kicker">
                      <span className="mini-dot mint-dot" /> MODEL QUALITY
                    </div>
                    <h2>Honest evaluation</h2>
                    <p className="panel-description">{evaluation.note}</p>
                  </div>
                </div>
                {evaluation.mape_note ? (
                  <p className="panel-description mt-10">{evaluation.mape_note}</p>
                ) : null}
                {result.data.warning ? (
                  <WarningList warnings={[result.data.warning]} />
                ) : null}
                {result.data.notes.length ? (
                  <ul className="note-list">
                    {result.data.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            </>
          ) : null}

          <section className="charts-matrix mt-15">
            <ChartPanel
              kicker="ACTUAL VS PREDICTED"
              title="Hold-out performance and forecast"
              description="Solid line = actual sales, dashed line = model predictions, dotted line = naive baseline."
              tone="violet"
              footer="Generated in Python with Plotly · hover to inspect exact values"
            >
              <PlotlyChart figure={result.figure} height={360} />
            </ChartPanel>

            <ChartPanel
              kicker="FORECAST VALUES"
              title="Predicted monthly sales"
              description="Values are clamped at zero — negative linear extrapolations are not allowed."
              tone="mint"
              footer={`${result.data.model} · baseline ${result.data.baseline}`}
            >
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th>Predicted sales</th>
                      <th>Raw model output</th>
                      <th>Clipped</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.data.forecasts.map((row) => (
                      <tr key={row.month}>
                        <td className="date-cell">{row.month}</td>
                        <td>{formatNumber(row.predicted_sales, 2)}</td>
                        <td className="date-cell">{formatNumber(row.raw_prediction, 2)}</td>
                        <td>
                          {row.raw_prediction < 0 ? (
                            <span className="chip">Clamped to 0</span>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ChartPanel>
          </section>
        </>
      ) : (
        <section className="panel view-panel">
          <StateBlock
            kind="empty"
            title="No forecast yet"
            message="Pick the date and sales columns, choose a horizon and run the forecast. Historical months are used for training and the last months are held out for evaluation."
          />
        </section>
      )}
    </>
  );
}
