'use client';

import {
  AlertTriangle,
  ArrowUpRight,
  Inbox,
  RefreshCw,
  ShieldAlert,
  X,
} from 'lucide-react';
import type { ReactNode } from 'react';

export function formatNumber(
  value: number | null | undefined,
  maximumFractionDigits = 0,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';

  return new Intl.NumberFormat('en-US', { maximumFractionDigits }).format(value);
}

export function formatCompact(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';

  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}k`;

  return formatNumber(value, 1);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) return '—';

  return parsed.toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

const sparkColors: Record<string, string> = {
  violet: '#8C7DF6',
  mint: '#31B6A5',
  amber: '#E8B35D',
  rose: '#E8848D',
};

export function Sparkline({ values, tone = 'violet' }: { values: number[]; tone?: string }) {
  if (values.length < 2) return null;

  const max = Math.max(...values);
  const min = Math.min(...values);
  const span = max - min || 1;

  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * 100;
      const y = 34 - ((value - min) / span) * 30;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');

  return (
    <svg className="kpi-spark" viewBox="0 0 100 36" preserveAspectRatio="none" aria-hidden="true">
      <polyline
        points={points}
        fill="none"
        stroke={sparkColors[tone] ?? sparkColors.violet}
        strokeWidth="1.8"
        vectorEffect="non-scaling-stroke"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function KpiCard({
  label,
  value,
  icon,
  tone = 'violet',
  hint,
  spark,
}: {
  label: string;
  value: string;
  icon: ReactNode;
  tone?: 'violet' | 'mint' | 'amber' | 'rose';
  hint?: string;
  spark?: number[];
}) {
  return (
    <div className="kpi-card">
      <div className="kpi-top">
        <span>{label}</span>
        <span className={`kpi-icon ${tone}`}>{icon}</span>
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-bottom">
        {hint ? <span className="kpi-detail">{hint}</span> : null}
      </div>
      {spark && spark.length > 1 ? <Sparkline values={spark} tone={tone} /> : null}
    </div>
  );
}

export function StateBlock({
  kind,
  title,
  message,
  action,
}: {
  kind: 'loading' | 'error' | 'empty';
  title: string;
  message?: string;
  action?: ReactNode;
}) {
  return (
    <div className={`state-block state-${kind}`}>
      {kind === 'loading' ? <span className="spinner" aria-hidden="true" /> : null}
      {kind === 'error' ? <ShieldAlert size={20} aria-hidden="true" /> : null}
      {kind === 'empty' ? <Inbox size={20} aria-hidden="true" /> : null}
      <strong>{title}</strong>
      {message ? <p>{message}</p> : null}
      {action ? <div className="state-action">{action}</div> : null}
    </div>
  );
}

export function WarningList({ warnings }: { warnings: string[] }) {
  const messages = warnings.filter(Boolean);

  if (!messages.length) return null;

  return (
    <div className="warning-list" role="status">
      {messages.map((warning) => (
        <div key={warning}>
          <AlertTriangle size={13} aria-hidden="true" />
          <span>{warning}</span>
        </div>
      ))}
    </div>
  );
}

export function FieldSelect({
  label,
  value,
  onChange,
  options,
  placeholder = 'Not selected',
  disabled,
  ariaLabel,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  disabled?: boolean;
  ariaLabel?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <span className="field-control">
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
          aria-label={ariaLabel ?? label}
        >
          <option value="">{placeholder}</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </span>
    </label>
  );
}

export function TextField({
  label,
  value,
  onChange,
  type = 'text',
  ariaLabel,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  ariaLabel?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <span className="field-control field-control-input">
        <input
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-label={ariaLabel ?? label}
        />
      </span>
    </label>
  );
}

export function Chip({
  children,
  onClear,
}: {
  children: ReactNode;
  onClear?: () => void;
}) {
  return (
    <span className="chip">
      {children}
      {onClear ? (
        <button type="button" onClick={onClear} aria-label="Clear filter">
          <X size={11} />
        </button>
      ) : null}
    </span>
  );
}

export function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}

export function ChartPanel({
  kicker,
  title,
  description,
  tone = 'violet',
  action,
  children,
  footer,
}: {
  kicker: string;
  title: string;
  description?: string;
  tone?: 'violet' | 'mint' | 'amber' | 'rose';
  action?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="panel view-panel">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">
            <span className={`mini-dot ${tone}-dot`} /> {kicker}
          </div>
          <h2>{title}</h2>
          {description ? <p className="panel-description">{description}</p> : null}
        </div>
        {action}
      </div>
      {children}
      {footer ? <div className="chart-footer">{footer}</div> : null}
    </div>
  );
}

export function RefreshButton({
  onClick,
  disabled,
  label = 'Refresh',
}: {
  onClick: () => void;
  disabled?: boolean;
  label?: string;
}) {
  return (
    <button
      type="button"
      className="button button-secondary button-small"
      onClick={onClick}
      disabled={disabled}
    >
      <RefreshCw size={14} /> {label}
    </button>
  );
}

export function UpRight() {
  return <ArrowUpRight size={13} aria-hidden="true" />;
}
