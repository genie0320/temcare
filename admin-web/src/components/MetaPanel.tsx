interface MetaPanelProps {
  id: string
  createdAt: string
  updatedAt: string
  updatedBy: string
}

function formatDateTime(iso: string): string {
  if (!iso) return '—'
  return iso.replace('T', ' ').slice(0, 16)
}

// docs/05_screen_conventions.md §B-4·5: ID는 여기서만 노출. 생성일시·최종수정·수정자 항상 표시.
export function MetaPanel({ id, createdAt, updatedAt, updatedBy }: MetaPanelProps) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>정보</h2>
      </div>
      <div className="card-body">
        <div className="side-row">
          <span className="k">생성</span>
          <span className="v">{formatDateTime(createdAt)}</span>
        </div>
        <div className="side-row">
          <span className="k">최종수정</span>
          <span className="v">{formatDateTime(updatedAt)}</span>
        </div>
        <div className="side-row">
          <span className="k">수정자</span>
          <span className="v">{updatedBy || '—'}</span>
        </div>
        <div className="side-row">
          <span className="k">ID</span>
          <span className="v">{id || '(저장 시 생성)'}</span>
        </div>
      </div>
    </div>
  )
}
