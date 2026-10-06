import type { ReactNode } from 'react'

export function StatChip(props: {
  label: string
  value: ReactNode
  hint?: string
  tone?: 'ok' | 'warn' | 'bad' | 'plain'
}) {
  const tone = props.tone ?? 'plain'
  return (
    <div className={`chip tone-${tone}`} title={props.hint}>
      <div className="chip-value">{props.value}</div>
      <div className="chip-label">{props.label}</div>
    </div>
  )
}
