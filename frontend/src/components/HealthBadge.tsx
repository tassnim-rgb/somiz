import { bandOf } from '../types'

// Coloured health badge from the Phase 4 index. Null = WARMUP or NO_READING
// (never fabricated).
export function HealthBadge(props: { hi: number | null }) {
  const band = bandOf(props.hi)
  if (!band) {
    return (
      <span className="badge" style={{ backgroundColor: '#eeeeee', color: '#616161' }}>
        Pas de lecture
      </span>
    )
  }
  return (
    <span className="badge" style={{ backgroundColor: band.color, color: '#ffffff' }}>
      {band.labelFr} {Math.round(props.hi ?? 0)}
    </span>
  )
}