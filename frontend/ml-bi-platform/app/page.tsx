'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  ArrowRight,
  Bell,
  BrainCircuit,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  CloudUpload,
  Database,
  Download,
  FileSpreadsheet,
  LayoutDashboard,
  Menu,
  MoreHorizontal,
  Plus,
  Settings2,
  ShieldAlert,
  Upload,
  X,
  Zap,
} from 'lucide-react';

import { api, ApiError, type Dataset } from '@/lib/api';
import { downloadCsv, safeFilename } from '@/lib/csv';
import UploadForm from '@/components/UploadForm';
import OverviewView from '@/components/views/OverviewView';
import DatasetsView from '@/components/views/DatasetsView';
import AnalyticsView from '@/components/views/AnalyticsView';
import ForecastView from '@/components/views/ForecastView';
import ReportsView from '@/components/views/ReportsView';

const navItems = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Datasets', icon: Database },
  { label: 'Analytics', icon: Activity },
  { label: 'ML predictions', icon: BrainCircuit },
  { label: 'Reports', icon: FileSpreadsheet },
];

const viewMeta: Record<string, { title: string; subtitle: string; eyebrow: string }> = {
  Overview: {
    title: 'Good morning, Alex',
    subtitle: "Here's what's happening with your business today.",
    eyebrow: 'BUSINESS OVERVIEW',
  },
  Datasets: {
    title: 'Datasets',
    subtitle: 'Upload, validate and profile the data behind your dashboards.',
    eyebrow: 'DATA MANAGEMENT',
  },
  Analytics: {
    title: 'Analytics',
    subtitle: 'Filter raw rows and generate interactive charts in Python.',
    eyebrow: 'INTERACTIVE ANALYTICS',
  },
  'ML predictions': {
    title: 'ML predictions',
    subtitle: 'Forecast sales with an honest, baseline-comparison evaluation.',
    eyebrow: 'PREDICTIVE ANALYTICS',
  },
  Reports: {
    title: 'Reports',
    subtitle: 'Summaries, method notes and exports for the selected dataset.',
    eyebrow: 'REPORTING',
  },
};

type Notice = { text: string; kind: 'success' | 'error' };

export default function Home() {
  const [activeNav, setActiveNav] = useState('Overview');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [datasetsError, setDatasetsError] = useState('');
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [loadingSample, setLoadingSample] = useState(false);
  const [exporting, setExporting] = useState(false);

  const notify = useCallback((text: string, kind: Notice['kind'] = 'success') => {
    setNotice({ text, kind });
  }, []);

  const loadDatasets = useCallback(async (preferId?: string) => {
    setLoadingDatasets(true);

    try {
      const response = await api.listDatasets();

      setDatasets(response.datasets);
      setDatasetsError('');
      setApiOnline(true);
      setSelectedId((previous) => {
        const wanted = preferId ?? previous;

        if (wanted && response.datasets.some((dataset) => dataset.id === wanted)) {
          return wanted;
        }

        return response.datasets[0]?.id ?? null;
      });
    } catch (error) {
      setApiOnline(false);
      setDatasetsError(
        error instanceof ApiError ? error.message : 'Failed to load datasets.',
      );
    } finally {
      setLoadingDatasets(false);
    }
  }, []);

  useEffect(() => {
    void loadDatasets();
  }, [loadDatasets]);

  const handleUploaded = useCallback(
    async (dataset: Dataset) => {
      setShowUpload(false);
      await loadDatasets(dataset.id);
      setActiveNav('Datasets');
      notify(
        `Imported “${dataset.name}” · ${dataset.row_count} rows, ${dataset.column_count} columns. It is now the selected dataset.`,
      );
    },
    [loadDatasets, notify],
  );

  const loadSampleDataset = useCallback(async () => {
    setLoadingSample(true);

    try {
      const response = await api.loadSampleDataset();

      await loadDatasets(response.dataset.id);
      notify(
        `Loaded sample dataset “${response.dataset.name}” · ${response.dataset.row_count} rows.`,
      );
    } catch (error) {
      notify(
        error instanceof ApiError
          ? `Could not load the sample dataset: ${error.message}`
          : 'Could not load the sample dataset.',
        'error',
      );
    } finally {
      setLoadingSample(false);
    }
  }, [loadDatasets, notify]);

  const exportReport = useCallback(async () => {
    if (!selectedId) {
      notify('Select a dataset before exporting a report.', 'error');
      return;
    }

    setExporting(true);

    try {
      const response = await api.getDatasetPreview(selectedId, 100);
      const dataset = datasets.find((item) => item.id === selectedId);

      downloadCsv(
        safeFilename(dataset?.name ?? response.data.name, 'preview-export.csv'),
        response.data.columns,
        response.data.rows,
      );
      notify(
        `Exported ${response.data.rows.length} rows from “${dataset?.name ?? response.data.name}” as CSV.`,
      );
    } catch (error) {
      notify(
        error instanceof ApiError ? `Export failed: ${error.message}` : 'Export failed.',
        'error',
      );
    } finally {
      setExporting(false);
    }
  }, [datasets, notify, selectedId]);

  const meta = viewMeta[activeNav] ?? viewMeta.Overview;
  const apiLabel =
    apiOnline === null ? 'Checking API…' : apiOnline ? 'API connected' : 'API unreachable';

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <Activity size={21} strokeWidth={2.7} />
          </div>
          <div>
            <div className="brand-name">
              northstar<span>.</span>
            </div>
            <div className="brand-caption">INTELLIGENCE PLATFORM</div>
          </div>
          <button
            type="button"
            className="mobile-close icon-button"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>
        <div className="workspace-switch">
          <div className="workspace-avatar">A</div>
          <div className="workspace-copy">
            <strong>Acme Commerce</strong>
            <span>Growth workspace</span>
          </div>
          <ChevronDown size={15} className="muted-icon" />
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="main-nav">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <button
                type="button"
                key={item.label}
                onClick={() => {
                  setActiveNav(item.label);
                  setMobileOpen(false);
                }}
                className={`nav-item ${activeNav === item.label ? 'active' : ''}`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
                {item.label === 'ML predictions' && <span className="nav-new">NEW</span>}
              </button>
            );
          })}
        </nav>
        <div className="nav-label tools-label">DATA &amp; TOOLS</div>
        <button type="button" className="nav-item" onClick={() => setShowUpload(true)}>
          <CloudUpload size={18} />
          <span>Import data</span>
          <Plus size={15} className="nav-trailing" />
        </button>
        <button
          type="button"
          className="nav-item"
          onClick={() =>
            setActiveNav('Datasets')
          }
        >
          <Database size={18} />
          <span>Data sources</span>
        </button>
        <div className="sidebar-spacer" />
        <div className="plan-card">
          <div className="plan-icon">
            <Zap size={16} />
          </div>
          <div className="plan-title">
            {datasets.length ? 'Live data connected' : 'Your workspace is ready'}
          </div>
          <p>
            {datasets.length
              ? 'KPIs and charts are computed from your stored datasets on every refresh.'
              : 'Import a CSV or XLSX file to compute live KPIs and charts.'}
          </p>
          <button type="button" onClick={() => setShowUpload(true)}>
            Add your data <ArrowRight size={14} />
          </button>
          <div className="plan-progress">
            <span style={{ width: `${Math.min(datasets.length, 3) * 33.4}%` }} />
          </div>
          <div className="plan-foot">
            <span>Workspace datasets</span>
            <span>{datasets.length} available</span>
          </div>
        </div>
        <div className="sidebar-bottom">
          <button
            type="button"
            className="nav-item"
            onClick={() => notify('Settings are not part of this build yet.')}
          >
            <Settings2 size={18} />
            <span>Settings</span>
          </button>
          <button
            type="button"
            className="nav-item"
            onClick={() => notify(`Backend API: ${api.baseUrl}`)}
          >
            <CircleHelp size={18} />
            <span>Help &amp; support</span>
          </button>
          <div className="user-profile">
            <div className="user-avatar">AS</div>
            <div className="user-copy">
              <strong>Alex Morgan</strong>
              <span>Workspace admin</span>
            </div>
            <MoreHorizontal size={19} className="muted-icon" />
          </div>
        </div>
      </aside>

      {mobileOpen && (
        <button
          type="button"
          className="mobile-overlay"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation"
        />
      )}

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="mobile-menu icon-button"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
            <div className="breadcrumb">
              Workspace <ChevronRight size={14} /> <strong>{activeNav}</strong>
            </div>
          </div>
          <div className="topbar-actions">
            <div className={`live-status ${apiOnline === false ? 'live-status-offline' : ''}`}>
              <span /> {apiLabel}
            </div>
            <button
              type="button"
              className="icon-button notification-button"
              aria-label="Notifications"
              onClick={() =>
                notify(
                  notice
                    ? 'Latest message is shown at the top of the page.'
                    : 'No new alerts. Import a dataset to get started.',
                )
              }
            >
              <Bell size={18} />
              <i />
            </button>
            <div className="top-avatar">AM</div>
          </div>
        </header>

        <div className="content-wrap">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-dot" /> {meta.eyebrow}{' '}
                <span className="eyebrow-divider">/</span>{' '}
                {datasets.find((item) => item.id === selectedId)?.name ?? 'NO DATASET'}
              </div>
              <h1>{meta.title}</h1>
              <p className="page-subtitle">{meta.subtitle}</p>
            </div>
            <div className="heading-actions">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setShowUpload(true)}
              >
                <Upload size={16} /> Import data
              </button>
              <button
                type="button"
                className="button button-primary"
                onClick={exportReport}
                disabled={exporting || !selectedId}
              >
                <Download size={16} /> {exporting ? 'Exporting…' : 'Export report'}
              </button>
            </div>
          </div>

          {notice && (
            <div className={`notice ${notice.kind === 'error' ? 'notice-error' : ''}`}>
              <div>
                {notice.kind === 'error' ? <ShieldAlert size={16} /> : <Check size={16} />}
                {notice.text}
              </div>
              <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss">
                <X size={16} />
              </button>
            </div>
          )}

          {activeNav === 'Overview' && (
            <OverviewView
              datasets={datasets}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onRequestUpload={() => setShowUpload(true)}
              onOpenAnalytics={() => setActiveNav('Analytics')}
              onLoadSample={loadSampleDataset}
              loadingSample={loadingSample}
            />
          )}

          {activeNav === 'Datasets' && (
            <DatasetsView
              datasets={datasets}
              selectedId={selectedId}
              onSelect={setSelectedId}
              loading={loadingDatasets}
              error={datasetsError}
              onReload={() => void loadDatasets()}
              onUploaded={handleUploaded}
              onLoadSample={loadSampleDataset}
              loadingSample={loadingSample}
            />
          )}

          {activeNav === 'Analytics' && (
            <AnalyticsView
              datasets={datasets}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}

          {activeNav === 'ML predictions' && (
            <ForecastView
              datasets={datasets}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}

          {activeNav === 'Reports' && (
            <ReportsView
              datasets={datasets}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}

          <footer className="page-footer">
            <span>© 2025 Northstar Intelligence</span>
            <span>
              <span className="footer-status-dot" /> Your data stays in your workspace
            </span>
            <button type="button" onClick={() => notify(`Backend API: ${api.baseUrl}`)}>
              API status <span className="api-status-dot" /> {apiLabel}
            </button>
          </footer>
        </div>
      </main>

      {showUpload && (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowUpload(false);
          }}
        >
          <div
            className="upload-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="upload-title"
          >
            <div className="modal-top">
              <div className="modal-icon">
                <CloudUpload size={22} />
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={() => setShowUpload(false)}
                aria-label="Close upload dialog"
              >
                <X size={18} />
              </button>
            </div>
            <h2 id="upload-title">Bring your data to life</h2>
            <p>Upload a CSV or XLSX file to compute live KPIs and charts from its rows.</p>
            <UploadForm onUploaded={handleUploaded} />
            <div className="modal-actions">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setShowUpload(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="button button-primary"
                onClick={() => {
                  setShowUpload(false);
                  void loadSampleDataset();
                }}
                disabled={loadingSample}
              >
                {loadingSample ? 'Loading…' : 'Use sample data'} <ArrowRight size={15} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
