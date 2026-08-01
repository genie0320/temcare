import { useState } from 'react'
import type { CandidateItem } from '../types/temType'
import { PickerModal } from './PickerModal'

interface ReferencePickListProps {
  label: string
  ids: string[]
  candidates: CandidateItem[]
  onChange: (ids: string[]) => void
}

// CuratedPickList와 달리 약점 필터가 없다 — 요법관리(adm_024) 참고정보(식품군·혈자리·제품)는
// 마스터 전체에서 자유롭게 선택한다(프로토타입 REFMETA와 동일).
export function ReferencePickList({ label, ids, candidates, onChange }: ReferencePickListProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const byId = new Map(candidates.map((c) => [c.id, c]))

  function remove(id: string) {
    onChange(ids.filter((x) => x !== id))
  }

  return (
    <div>
      {ids.length === 0 ? (
        <span className="muted">없음</span>
      ) : (
        ids.map((id) => {
          const info = byId.get(id)
          return (
            <div key={id} className="pickrow">
              <span className="grip">⠿</span>
              {info?.polarity && <span className={`pill ${info.polarity === '권장' ? 'a' : 'c'}`}>{info.polarity}</span>}
              <span className="nm">{info?.name ?? id}</span>
              <span className="ds">{info?.sub}</span>
              <button type="button" className="rm" onClick={() => remove(id)}>
                삭제
              </button>
            </div>
          )
        })
      )}
      <button type="button" className="addbtn" style={{ marginTop: ids.length ? 8 : 0 }} onClick={() => setModalOpen(true)}>
        + {label} 추가
      </button>
      {modalOpen && (
        <PickerModal
          title={label}
          items={candidates}
          selectedIds={ids}
          emptyHint="등록된 항목이 없다."
          onApply={(next) => {
            onChange(next)
            setModalOpen(false)
          }}
          onClose={() => setModalOpen(false)}
        />
      )}
    </div>
  )
}
