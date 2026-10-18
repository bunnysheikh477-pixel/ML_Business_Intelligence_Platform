const RAW_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000/api/v1';

export const API_BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export type QueryValue = string | number | boolean | null | undefined;

function buildUrl(path: string, params?: Record<string, QueryValue>): string {
  const url = new URL(`${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`);

  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    url.searchParams.set(key, String(value));
  });

  return url.toString();
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = (body as { detail?: unknown }).detail;

    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item?.msg === 'string' ? item.msg : JSON.stringify(item)))
        .join('; ');
    }
    if (detail) return JSON.stringify(detail);
  } catch {
    /* fall through to the generic message */
  }

  return `Request failed with status ${response.status}.`;
}

async function request<T>(
  path: string,
  options: { method?: string; params?: Record<string, QueryValue>; body?: BodyInit } = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(buildUrl(path, options.params), {
      method: options.method ?? 'GET',
      body: options.body,
      cache: 'no-store',
    });
  } catch {
    throw new ApiError(
      `Cannot reach the API at ${API_BASE_URL}. Start the FastAPI backend and check NEXT_PUBLIC_API_BASE_URL.`,
      0,
    );
  }

  if (!response.ok) {
    throw new ApiError(await readError(response), response.status);
  }

  return (await response.json()) as T;
}

export type Dataset = {
  id: string;
  name: string;
  file_type: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  columns: string[];
  created_at: string;
};

export type DatasetColumnProfile = {
  name: string;
  dtype: string;
  missing_values: number;
  missing_percentage: number;
  unique_values: number;
};

export type DatasetProfile = {
  dataset_id: string;
  name: string;
  row_count: number;
  column_count: number;
  columns: DatasetColumnProfile[];
  duplicate_rows: number;
};

export type DatasetDetails = Dataset & {
  detected_columns: Record<string, string | null>;
  filters: { date: boolean; category: boolean; region: boolean };
  profile: Omit<DatasetProfile, 'dataset_id' | 'name'>;
};

export type PreviewRow = Record<string, string | number | boolean | null>;

export type DatasetPreview = {
  dataset_id: string;
  name: string;
  columns: string[];
  rows: PreviewRow[];
};

export type PlotlyFigure = {
  data: unknown[];
  layout: Record<string, unknown>;
};

export type ChartSpec = {
  key: string;
  title: string;
  description?: string;
  type?: string;
  status: 'ready' | 'unavailable';
  reason?: string;
  figure?: PlotlyFigure;
};

export type ChartsResponse = {
  success: boolean;
  cached: boolean;
  dataset: { id: string; name: string };
  detected_columns: Record<string, string | null>;
  available_columns: string[];
  filters: Record<string, string | null>;
  charts: ChartSpec[];
  warnings: string[];
};

export type ColumnMapping = {
  date_column?: string | null;
  sales_column?: string | null;
  category_column?: string | null;
  region_column?: string | null;
  profit_column?: string | null;
  product_column?: string | null;
  quantity_column?: string | null;
};

export type AnalysisFilters = {
  date_from?: string | null;
  date_to?: string | null;
  category_value?: string | null;
  region_value?: string | null;
};

export type Kpis = {
  total_rows: number;
  total_columns: number;
  total_revenue: number | null;
  total_orders: number;
  orders_count_method: string;
  average_order_value: number | null;
  total_profit: number | null;
  profit_margin_percent: number | null;
  total_quantity: number | null;
  revenue_column: string | null;
  order_id_column: string | null;
  profit_column: string | null;
  quantity_column: string | null;
  available_columns: string[];
  data_quality: {
    rows: number;
    columns: number;
    total_cells: number;
    missing_cells: number;
    missing_percentage: number;
    columns_with_missing: { name: string; missing_values: number; missing_percentage: number }[];
    columns_missing_count: number;
    empty_columns: string[];
    duplicate_rows: number;
  };
  calculation_notes: string[];
};

export type AnalyticsOverview = {
  success: boolean;
  dataset: { id: string; name: string };
  kpis: Kpis;
  monthly_revenue: { month: string; revenue: number }[];
  category_sales: { category: string; revenue: number; share_percent: number }[];
  region_sales: { region: string; revenue: number; share_percent: number }[];
  top_products: {
    product: string;
    revenue: number;
    share_percent: number;
    quantity?: number | null;
  }[];
  detected_columns: Record<string, string | null>;
  available_columns: string[];
  filters: Record<string, string | null>;
  facets: { category: string[]; region: string[] };
  rows_analyzed: number;
  warnings: string[];
};

export type ForecastResult = {
  model: string;
  baseline: string;
  target: string;
  date_column: string;
  frequency: string;
  historical_months: number;
  history: { month: string; actual_sales: number }[];
  forecasts: { month: string; predicted_sales: number; raw_prediction: number }[];
  evaluation:
    | {
        status: 'evaluated';
        method: string;
        train_months: number;
        test_months: number;
        model_metrics: { mae: number; rmse: number; mape_percent: number | null };
        baseline: {
          name: string;
          description: string;
          metrics: { mae: number; rmse: number; mape_percent: number | null };
        };
        comparison: { model_better_than_baseline: boolean; mae_improvement_percent: number | null };
        actual_vs_predicted: {
          month: string;
          actual: number;
          predicted: number;
          baseline_prediction: number;
        }[];
        mape_note: string | null;
        note: string;
      }
    | {
        status: 'insufficient_data';
        available_months: number;
        required_months: number;
        message: string;
      };
  warnings: string[];
  notes: string[];
  warning: string | null;
};

export type ForecastResponse = {
  success: boolean;
  dataset_id: string;
  dataset: { id: string; name: string };
  columns: { date_column: string; sales_column: string };
  data: ForecastResult;
  figure: PlotlyFigure;
};

function uploadWithProgress<T>(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const request_ = new XMLHttpRequest();
    request_.open('POST', buildUrl('/datasets/upload'));
    request_.responseType = 'json';

    request_.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    request_.onload = () => {
      const body = request_.response as { detail?: unknown } | null;

      if (request_.status >= 200 && request_.status < 300) {
        onProgress?.(100);
        resolve(body as T);
        return;
      }

      const detail = body?.detail;
      reject(
        new ApiError(
          typeof detail === 'string'
            ? detail
            : `Upload failed with status ${request_.status}.`,
          request_.status,
        ),
      );
    };

    request_.onerror = () => {
      reject(
        new ApiError(
          `Cannot reach the API at ${API_BASE_URL}. Start the FastAPI backend and check NEXT_PUBLIC_API_BASE_URL.`,
          0,
        ),
      );
    };

    const form = new FormData();
    form.append('file', file);
    request_.send(form);
  });
}

export const api = {
  baseUrl: API_BASE_URL,

  listDatasets: () =>
    request<{ success: boolean; datasets: Dataset[] }>('/datasets/'),

  loadSampleDataset: () =>
    request<{ success: boolean; dataset: Dataset }>('/datasets/sample', {
      method: 'POST',
    }),

  uploadDataset: (file: File, onProgress?: (percent: number) => void) =>
    uploadWithProgress<{ success: boolean; dataset: Dataset }>(file, onProgress),

  getDatasetDetails: (datasetId: string) =>
    request<{ success: boolean; dataset: DatasetDetails }>(`/datasets/${datasetId}`),

  getDatasetPreview: (datasetId: string, limit = 25) =>
    request<{ success: boolean; data: DatasetPreview }>(
      `/datasets/${datasetId}/preview`,
      { params: { limit } },
    ),

  getDatasetProfile: (datasetId: string) =>
    request<{ success: boolean; profile: DatasetProfile }>(
      `/datasets/${datasetId}/profile`,
    ),

  getOverview: (
    datasetId: string,
    mapping: ColumnMapping = {},
    filters: AnalysisFilters = {},
  ) =>
    request<AnalyticsOverview>(`/analytics/${datasetId}/overview`, {
      params: { ...mapping, ...filters },
    }),

  getCharts: (
    datasetId: string,
    mapping: ColumnMapping = {},
    filters: AnalysisFilters = {},
  ) =>
    request<ChartsResponse>(`/charts/${datasetId}`, {
      params: { ...mapping, ...filters },
    }),

  runForecast: (
    datasetId: string,
    options: { dateColumn?: string | null; salesColumn?: string | null; periods?: number },
  ) =>
    request<ForecastResponse>(`/ml/${datasetId}/forecast`, {
      method: 'POST',
      params: {
        date_column: options.dateColumn ?? undefined,
        sales_column: options.salesColumn ?? undefined,
        periods: options.periods ?? 3,
      },
    }),
};
