'use client';

import type { ChartSpec } from '@/lib/api';
import PlotlyChart from '@/components/PlotlyChart';
import { ChartPanel, StateBlock } from '@/components/ui';

export default function ChartCard({
  chart,
  kicker,
  tone = 'violet',
  height = 330,
  footer,
}: {
  chart: ChartSpec;
  kicker?: string;
  tone?: 'violet' | 'mint' | 'amber' | 'rose';
  height?: number;
  footer?: string;
}) {
  return (
    <ChartPanel
      kicker={kicker ?? (chart.type ?? 'chart').toUpperCase()}
      title={chart.title}
      description={chart.description}
      tone={tone}
      footer={
        footer ??
        (chart.status === 'ready'
          ? 'Generated in Python with Plotly · interactive hover and zoom'
          : undefined)
      }
    >
      {chart.status === 'ready' && chart.figure ? (
        <PlotlyChart figure={chart.figure} height={height} />
      ) : (
        <StateBlock
          kind="empty"
          title="Chart unavailable"
          message={chart.reason ?? 'This dataset does not support this chart.'}
        />
      )}
    </ChartPanel>
  );
}
