// Loose typings for the Plotly stack (plotly.js-dist-min bundles its own
// JS + CSS; react-plotly.js is a thin React wrapper). Charts are a display
// layer only: every series comes from the SIMULATED backend.

declare module 'plotly.js-dist-min' {
  export interface Data {
    [key: string]: unknown
  }
  export interface Layout {
    [key: string]: unknown
  }
  export interface Config {
    [key: string]: unknown
  }
}

declare module 'react-plotly.js' {
  import type * as React from 'react'
  import type { Config, Data, Layout } from 'plotly.js-dist-min'
  const Plot: React.FC<{
    data: Data[]
    layout?: Partial<Layout>
    config?: Partial<Config>
    style?: React.CSSProperties
    useResizeHandler?: boolean
    className?: string
  }>
  export default Plot
}