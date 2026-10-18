'use client';

import { useRef, useState } from 'react';
import { CloudUpload, Database, ShieldCheck, Upload } from 'lucide-react';

import { api, ApiError, type Dataset } from '@/lib/api';

export default function UploadForm({
  onUploaded,
  onError,
}: {
  onUploaded: (dataset: Dataset) => void;
  onError?: (message: string) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [hovering, setHovering] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');

  async function handleFile(file?: File) {
    if (!file) return;

    const name = file.name.toLowerCase();
    const allowed = name.endsWith('.csv') || name.endsWith('.xlsx');

    if (!allowed) {
      setError('Only .csv and .xlsx files are supported.');
      return;
    }

    setUploading(true);
    setError('');
    setProgress(0);

    try {
      const response = await api.uploadDataset(file, setProgress);
      onUploaded(response.dataset);
    } catch (uploadError) {
      const message =
        uploadError instanceof ApiError
          ? uploadError.message
          : 'Upload failed. Please try again.';
      setError(message);
      onError?.(message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        className={`drop-zone ${hovering ? 'drop-zone-hover' : ''}`}
        onClick={() => input.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setHovering(true);
        }}
        onDragLeave={() => setHovering(false)}
        onDrop={(event) => {
          event.preventDefault();
          setHovering(false);
          void handleFile(event.dataTransfer.files[0]);
        }}
        disabled={uploading}
      >
        <div className="drop-icon">
          <Upload size={21} />
        </div>
        <strong>{uploading ? 'Uploading…' : 'Click to browse or drag a CSV/XLSX file here'}</strong>
        <span>CSV and XLSX · up to 20 MB · validated on the server before storage</span>
        <span className="browse-label">{uploading ? 'Please wait' : 'Choose a file'}</span>
      </button>

      <input
        ref={input}
        type="file"
        accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        hidden
        onChange={(event) => {
          void handleFile(event.target.files?.[0]);
          event.target.value = '';
        }}
      />

      {uploading ? (
        <div className="progress-track" aria-label="Upload progress">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      ) : null}

      {error ? (
        <div className="warning-list mt-10" role="alert">
          <div>
            <CloudUpload size={13} />
            <span>{error}</span>
          </div>
        </div>
      ) : null}

      <div className="upload-info">
        <ShieldCheck size={15} />
        <span>
          Files are uploaded to the FastAPI backend, validated, stored and profiled.
          Dataset metadata is saved in MongoDB.
        </span>
      </div>

      <div className="upload-info">
        <Database size={15} />
        <span>KPIs and charts are always computed from the uploaded rows.</span>
      </div>
    </div>
  );
}
