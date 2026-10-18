'use client';

import { useEffect, useRef, useState } from 'react';
import type { PlotlyFigure } from '@/lib/api';

type PlotlyModule = typeof import('plotly.js-dist')['default'];

let plotlyLoader: Promise<PlotlyModule> | null = null;

function loadPlotly(): Promise<PlotlyModule> {
  if (!plotlyLoader) {
    plotlyLoader = import('plotly.js-dist').then((module) => {
      const resolved =
        (module as { default?: PlotlyModule }).default ??
        (module as unknown as PlotlyModule);

      if (typeof resolved?.react !== 'function') {
        throw new Error('plotly.js-dist did not expose a usable module.');
      }

      return resolved;
    });
  }

  return plotlyLoader;
}

export const PLOTLY_CONFIG = {
  responsive: true,
  displaylogo: false,
  displayModeBar: false,
  scrollZoom: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
};

export default function PlotlyChart({
  figure,
  height,
  className,
}: {
  figure: PlotlyFigure;
  height?: number;
  className?: string;
}) {
  const container = useRef<HTMLDivElement>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let disposed = false;
    const node = container.current;

    if (!node) return;

    (async () => {
      try {
        const Plotly = await loadPlotly();

        if (disposed) return;

        const layout = {
          autosize: true,
          ...figure.layout,
          ...(height ? { height } : {}),
        };

        await Plotly.react(node, figure.data, layout, PLOTLY_CONFIG);
      } catch {
        if (!disposed) {
          setError('The chart library could not be loaded in this browser.');
        }
      }
    })();

    return () => {
      disposed = true;

      void loadPlotly()
        .then((Plotly) => {
          try {
            Plotly.purge(node);
          } catch {
            /* node already detached */
          }
        })
        .catch(() => undefined);
    };
  }, [figure, height]);

  useEffect(() => {
    const node = container.current;

    if (!node || typeof ResizeObserver === 'undefined') return;

    const observer = new ResizeObserver(() => {
      void loadPlotly()
        .then((Plotly) => Plotly.Plots.resize(node))
        .catch(() => undefined);
    });

    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  if (error) {
    return <div className="state-block state-error">{error}</div>;
  }

  return (
    <div
      ref={container}
      className={className ?? 'plotly-host'}
      style={{ width: '100%', height: height ?? 340 }}
      aria-label="Interactive chart"
      role="img"
    />
  );
}
