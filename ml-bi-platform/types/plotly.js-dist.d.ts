declare module 'plotly.js-dist' {
  type PlotlyElement = HTMLElement;

  const Plotly: {
    react(
      element: PlotlyElement,
      data: unknown[],
      layout?: Record<string, unknown>,
      config?: Record<string, unknown>,
    ): Promise<unknown>;
    newPlot(
      element: PlotlyElement,
      data: unknown[],
      layout?: Record<string, unknown>,
      config?: Record<string, unknown>,
    ): Promise<unknown>;
    purge(element: PlotlyElement): void;
    Plots: {
      resize(element: PlotlyElement): Promise<unknown>;
    };
  };

  export default Plotly;
}
