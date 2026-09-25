import Plot from 'react-plotly.js'
import type { CSSProperties } from 'react'

// Small wrapper so pages stay declarative. Charts render SIMULATED data.
export function Chart(props: {
  data: Record<string, unknown>[]
  layout?: Record<string, unknown>
  style?: CSSProperties
}) {
  return (
    <Plot
      data={props.data as never}
      layout={{
        autosize: true,
        margin: { l: 48, r: 24, t: 32, b: 40 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'system-ui, sans-serif', size: 12 },
        ...props.layout,
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%', height: 340, ...props.style }}
      useResizeHandler
    />
  )
}