import type { ReactNode } from 'react'

// docs/05_screen_conventions.md §B: 좌 3/4 본문 + 우 1/4 사이드패널.
export function DetailLayout({ main, side }: { main: ReactNode; side: ReactNode }) {
  return (
    <div className="detail-wrap">
      <div>{main}</div>
      <div className="side">{side}</div>
    </div>
  )
}

export function Card({ title, sub, right, children }: { title?: string; sub?: string; right?: ReactNode; children: ReactNode }) {
  return (
    <div className="card">
      {title && (
        <div className="card-head">
          <h2>{title}</h2>
          {sub && <span className="sub">{sub}</span>}
          {right && <div className="r">{right}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  )
}
