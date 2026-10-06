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
        font: { family: "'IBM Plex Sans', system-ui, sans-serif", size: 12, color: '#8fa2b5' },
        ...props.layout,
        xaxis: { gridcolor: '#17202d', zerolinecolor: '#22303f', tickfont: { color: '#5d6e80' }, ...(props.layout?.xaxis as object) },
        yaxis: { gridcolor: '#17202d', zerolinecolor: '#22303f', tickfont: { color: '#5d6e80' }, ...(props.layout?.yaxis as object) },
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%', height: 340, ...props.style }}
      useResizeHandler
    />
  )
}