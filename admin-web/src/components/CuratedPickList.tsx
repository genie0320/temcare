import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { apiGet } from '../api/client'
import type { CandidateItem } from '../types/temType'
import { PickerModal } from './PickerModal'

interface CuratedPickListProps {
  label: string
  ids: string[]
  weaknessIds: string[]
  candidatesPath: string
  onChange: (ids: string[]) => void
}

// docs/02_architecture_constraints.md §7 큐레이션 — 선택한 약점 태그를 가진 카드/식품만 후보로 뜬다.
export function CuratedPickList({ label, ids, weaknessIds, candidatesPath, onChange }: CuratedPickListProps) {
  const [modalOpen, setModalOpen] = useState(false)

  const { data: candidates } = useQuery({
    queryKey: [candidatesPath, weaknessIds],
    queryFn: () => apiGet<CandidateItem[]>(`${candidatesPath}?weaknesses=${weaknessIds.join(',')}`),
    enabled: weaknessIds.length > 0,
  })
  const byId = new Map((candidates ?? []).map((c) => [c.id, c]))

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
          items={candidates ?? []}
          selectedIds={ids}
          emptyHint={weaknessIds.length ? '선택한 약점을 가진 항목이 없다.' : '먼저 위의 관련 약점을 선택할 것. 선택한 약점을 가진 항목만 노출된다.'}
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
