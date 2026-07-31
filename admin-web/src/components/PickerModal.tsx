import { useState } from 'react'
import type { CandidateItem } from '../types/temType'

interface PickerModalProps {
  title: string
  items: CandidateItem[]
  selectedIds: string[]
  emptyHint?: string
  onApply: (ids: string[]) => void
  onClose: () => void
}

// docs/05_screen_conventions.md §D 실피커 모달.
export function PickerModal({ title, items, selectedIds, emptyHint, onApply, onClose }: PickerModalProps) {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set(selectedIds))

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const filtered = items.filter((item) => {
    if (!query.trim()) return true
    const haystack = `${item.name} ${item.sub}`.toLowerCase()
    return haystack.includes(query.toLowerCase())
  })

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div className="modal-head">
          <span>{title} 추가</span>
          <button className="btn xs" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="modal-search">
          <input placeholder="검색" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <div className="modal-list">
          {items.length === 0 ? (
            <div className="hint" style={{ padding: '14px 2px' }}>
              {emptyHint ?? '먼저 관련 약점을 선택할 것. 선택한 약점을 가진 항목만 노출된다.'}
            </div>
          ) : filtered.length === 0 ? (
            <div className="hint" style={{ padding: '14px 2px' }}>
              검색 결과가 없다.
            </div>
          ) : (
            filtered.map((item) => (
              <label key={item.id} className="modal-item">
                <input type="checkbox" checked={selected.has(item.id)} onChange={() => toggle(item.id)} />
                {item.polarity && (
                  <span className={`pill ${item.polarity === '권장' ? 'a' : 'c'}`}>{item.polarity}</span>
                )}
                <b>{item.name}</b>
                {item.sub && <span className="muted"> · {item.sub}</span>}
              </label>
            ))
          )}
        </div>
        <div className="modal-foot">
          <button className="btn" onClick={onClose}>
            취소
          </button>
          <button className="btn primary" onClick={() => onApply([...selected])}>
            완료
          </button>
        </div>
      </div>
    </div>
  )
}
