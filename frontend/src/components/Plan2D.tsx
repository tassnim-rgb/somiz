import { useRef, useState } from 'react'
import type { Atelier, Equip, Zone } from '../data/ateliers'
import { STATUS_COLORS } from '../data/ateliers'
import { hexColor, STATUS_LABEL } from '../lib/sim'

// Wrap a zone title into lines that roughly fit the zone width (metres).
function wrapLabel(text: string, maxChars: number): string[] {
  const words = text.split(' ')
  const lines: string[] = []
  let cur = ''
  for (const w of words) {
    if (!cur) cur = w
    else if ((cur + ' ' + w).length <= maxChars) cur += ' ' + w
    else {
      lines.push(cur)
      cur = w
    }
  }
  if (cur) lines.push(cur)
  return lines.slice(0, 3)
}

function zoneLines(z: Zone): { lines: string[]; sub: string[]; fs: number } {
  const fs0 = 1.25
  const maxChars = Math.max(6, Math.floor((z.w * 0.85) / (fs0 * 0.6)))
  const lines = wrapLabel(z.name, maxChars)
  const sub = z.area ? [z.area.replace(/^S\s*=\s*/, '')] : []
  // shrink the font so the widest line (incl. unbreakable words) fits the zone
  const widest = Math.max(1, ...lines.map((l) => l.length), ...sub.map((l) => l.length))
  const fs = Math.max(0.62, Math.min(fs0, (z.w * 0.85) / (widest * 0.6)))
  return { lines, sub, fs }
}

interface Props {
  atelier: Atelier
  selectedId: string | null
  onSelect: (id: string | null) => void
}

// Top-down 2D SVG plan of one atelier: zones, machines, plan title.
// Machine positions are approximate OCR readings (P-01 ind. 01).
export function Plan2D({ atelier: a, selectedId, onSelect }: Props) {
  const frameRef = useRef<HTMLDivElement>(null)
  const [tip, setTip] = useState<{ x: number; y: number; text: string } | null>(null)

  const pad = 4
  const viewBox = `${-pad} ${-pad} ${a.w + pad * 2} ${a.d + pad * 2}`

  function hover(eq: Equip, e: React.MouseEvent) {
    const frame = frameRef.current
    if (!frame) return
    const r = frame.getBoundingClientRect()
    const x = e.clientX - r.left
    const y = e.clientY - r.top
    setTip({
      x: Math.min(x + 14, r.width - 230),
      y: Math.max(6, y - 12),
      text: `${eq.name} · ${STATUS_LABEL[eq.status]}`,
    })
  }

  return (
    <div className="plan-frame" ref={frameRef}>
      <svg viewBox={viewBox} preserveAspectRatio="xMidYMid meet" role="img"
        aria-label={`Plan de l'${a.name} — implantation approximative`}>
        <defs>
          <pattern id="plan-grid" width="5" height="5" patternUnits="userSpaceOnUse">
            <path d="M 5 0 L 0 0 0 5" fill="none" stroke="#101a24" strokeWidth="0.08" />
          </pattern>
        </defs>

        {/* building slab + survey grid */}
        <rect x="0" y="0" width={a.w} height={a.d} fill="url(#plan-grid)" />
        <rect
          x="0"
          y="0"
          width={a.w}
          height={a.d}
          fill="none"
          stroke="rgba(31,211,232,0.4)"
          strokeWidth="0.22"
        />

        {/* plan title block */}
        <text className="plan-title" x="0.6" y="-1.4" fontSize="1.7">
          {a.name.toUpperCase()} · {a.surface} · P-01 IND. 01
        </text>

        {/* zones */}
        {a.zones.map((z) => {
          const { lines, sub, fs } = zoneLines(z)
          const cx = z.x + z.w / 2
          const cz = z.z + z.d / 2
          const total = lines.length + sub.length
          const y0 = cz - ((total - 1) * (fs + 0.45)) / 2 + fs * 0.34
          return (
            <g key={z.name + z.x} className="zone-shape">
              <rect
                x={z.x}
                y={z.z}
                width={z.w}
                height={z.d}
                fill={hexColor(z.color)}
                stroke="rgba(31,211,232,0.22)"
                strokeWidth="0.12"
              />
              {lines.map((ln, i) => (
                <text
                  key={ln + i}
                  className="zone-text"
                  x={cx}
                  y={y0 + i * (fs + 0.45)}
                  fontSize={fs}
                  textAnchor="middle"
                  stroke="#05070a"
                  strokeWidth="0.3"
                  paintOrder="stroke"
                >
                  {ln}
                </text>
              ))}
              {sub.map((ln, i) => (
                <text
                  key={ln + i}
                  className="zone-sub"
                  x={cx}
                  y={y0 + (lines.length + i) * (fs + 0.45)}
                  fontSize={fs - 0.3}
                  textAnchor="middle"
                  stroke="#05070a"
                  strokeWidth="0.3"
                  paintOrder="stroke"
                >
                  {ln}
                </text>
              ))}
            </g>
          )
        })}

        {/* machines */}
        {a.equipment.map((eq) => (
          <rect
            key={eq.id}
            className="machine-shape"
            x={eq.x}
            y={eq.z}
            width={eq.w}
            height={eq.d}
            rx={0.3}
            fill={hexColor(STATUS_COLORS[eq.status])}
            fillOpacity={0.92}
            stroke={eq.id === selectedId ? '#1fd3e8' : '#05070a'}
            strokeWidth={eq.id === selectedId ? 0.45 : 0.14}
            onMouseMove={(e) => hover(eq, e)}
            onMouseLeave={() => setTip(null)}
            onClick={() => onSelect(eq.id)}
          >
            <title>{`${eq.name} — ${STATUS_LABEL[eq.status]} (état simulé)`}</title>
          </rect>
        ))}
      </svg>

      <div className="grid-label">
        SOMIZ-SPA · Arzew, Oran · implantation P-01 — positions approximatives · états simulés
      </div>

      {tip ? <div className="tooltip" style={{ left: tip.x, top: tip.y }}>{tip.text}</div> : null}
    </div>
  )
}
