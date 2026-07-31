import type { ContentStatus } from '../types/weakness'

interface PublishBoxProps {
  status: ContentStatus
  onStatusChange: (status: ContentStatus) => void
  onSave: () => void
  onDelete?: () => void
  saving?: boolean
  isNew?: boolean
}

// docs/05_screen_conventions.md §B-3: 게시 박스 = 상태 + 저장 + 삭제. 취소 버튼은 두지 않는다.
export function PublishBox({ status, onStatusChange, onSave, onDelete, saving, isNew }: PublishBoxProps) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>게시</h2>
      </div>
      <div className="card-body actions-col">
        <select className="selectbox" style={{ width: '100%' }} value={status} onChange={(e) => onStatusChange(e.target.value as ContentStatus)}>
          <option value="게시">게시</option>
          <option value="초안">초안</option>
          <option value="숨김">숨김</option>
        </select>
        <button className="btn primary" onClick={onSave} disabled={saving}>
          {saving ? '저장 중…' : '저장'}
        </button>
        {!isNew && onDelete && (
          <button className="btn danger" onClick={onDelete}>
            삭제
          </button>
        )}
      </div>
    </div>
  )
}
