import { useState } from 'react'

const BODY_STOPS = ['매우 마름', '마름', '보통', '비만', '매우 비만']

interface BodySliderProps {
  lo: number
  hi: number
  onChange: (lo: number, hi: number) => void
}

// docs/05_screen_conventions.md·spec adm_002 순서3 — 시작점→종료점을 순서대로 클릭해 범위를 고른다.
export function BodySlider({ lo, hi, onChange }: BodySliderProps) {
  const [pending, setPending] = useState<number | null>(null)

  function clickStop(i: number) {
    if (pending === null) {
      setPending(i)
      onChange(i, i)
    } else {
      onChange(Math.min(pending, i), Math.max(pending, i))
      setPending(null)
    }
  }

  const fillLeft = lo * 25
  const fillWidth = (hi - lo) * 25
  const rangeText = lo === hi ? BODY_STOPS[lo] : `${BODY_STOPS[lo]} ~ ${BODY_STOPS[hi]}`
  const guide = pending !== null ? '종료점을 클릭하세요.' : '시작점 → 종료점을 차례로 클릭하면 범위가 설정됩니다.'

  return (
    <div className="bodyslider">
      <div className="btrack">
        <div className="bfill" style={{ left: `${fillLeft}%`, width: `${fillWidth}%` }} />
        {BODY_STOPS.map((label, i) => (
          <button
            key={label}
            type="button"
            className={`bstop ${i >= lo && i <= hi ? 'on' : ''} ${pending === i ? 'pend' : ''}`}
            style={{ left: `${i * 25}%` }}
            onClick={() => clickStop(i)}
          >
            <span className="bdot" />
            <span className="blab">{label}</span>
          </button>
        ))}
      </div>
      <div className="hint" style={{ marginTop: 30 }}>
        {guide} 현재: <b>{rangeText}</b>
      </div>
    </div>
  )
}
