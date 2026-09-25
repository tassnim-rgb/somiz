import type { ReactNode } from 'react'

export function StatChip(props: {
  label: string
  value: ReactNode
  hint?: string
  tone?: 'ok' | 'warn' | 'bad' | 'plain'
}) {
  const tones: Record<string, string> = {
    ok: '#e8f5e9',
    warn: '#fff8e1',
    bad: '#ffebee',
    plain: '#f5f5f5',
  }
  return (
    <div
      className="chip"
      style={{ backgroundColor: tones[props.tone ?? 'plain'] }}
      title={props.hint}
    >
      <div className="chip-value">{props.value}</div>
      <div className="chip-label">{props.label}</div>
    </div>
  )
}