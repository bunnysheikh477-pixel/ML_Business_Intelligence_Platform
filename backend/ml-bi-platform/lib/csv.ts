export function csvCell(value: unknown): string {
  const text = value === null || value === undefined ? '' : String(value);

  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }

  return text;
}

export function rowsToCsv(
  columns: string[],
  rows: Record<string, unknown>[],
): string {
  const header = columns.map(csvCell).join(',');
  const body = rows
    .map((row) => columns.map((column) => csvCell(row[column])).join(','))
    .join('\n');

  return `${header}\n${body}`;
}

export function downloadCsv(
  filename: string,
  columns: string[],
  rows: Record<string, unknown>[],
): void {
  const blob = new Blob([rowsToCsv(columns, rows)], {
    type: 'text/csv;charset=utf-8;',
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');

  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function safeFilename(value: string, suffix: string): string {
  return `${value.replace(/[^\w.-]+/g, '-')}-${suffix}`;
}
