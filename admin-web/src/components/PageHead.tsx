import type { ReactNode } from 'react'
import { Link } from 'react-router'

interface PageHeadProps {
  title: string
  description?: string
  backTo?: string
  actions?: ReactNode
}

// docs/05_screen_conventions.md §B-2: '← 목록'은 타이틀 왼쪽에 둔다.
export function PageHead({ title, description, backTo, actions }: PageHeadProps) {
  return (
    <div className="page-head">
      {backTo && (
        <div className="backwrap">
          <Link to={backTo} className="btn ghost sm">
            ← 목록
          </Link>
        </div>
      )}
      <div className="titles">
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="actions">{actions}</div>}
    </div>
  )
}
