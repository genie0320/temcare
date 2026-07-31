import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { IllnessLink, IllnessOption } from '../types/temType'

interface IllnessRateRowsProps {
  rows: IllnessLink[]
  onChange: (rows: IllnessLink[]) => void
}

// spec adm_002 순서5 — 질환 선택 + % 입력 반복 행. 합계 100% 검증 없음(질환별 독립 발병율).
export function IllnessRateRows({ rows, onChange }: IllnessRateRowsProps) {
  const { data: options } = useQuery({
    queryKey: ['illness-options'],
    queryFn: () => apiGet<IllnessOption[]>('/content/illness-options/'),
  })

  function update(i: number, patch: Partial<IllnessLink>) {
    onChange(rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)))
  }

  function remove(i: number) {
    onChange(rows.filter((_, idx) => idx !== i))
  }

  function add() {
    onChange([...rows, { illness_id: '', pct: 0 }])
  }

  return (
    <div>
      {rows.map((row, i) => (
        <div key={i} className="pickrow">
          <select
            className="selectbox"
            style={{ maxWidth: 240 }}
            value={row.illness_id}
            onChange={(e) => update(i, { illness_id: e.target.value })}
          >
            <option value="">질환 선택</option>
            {(options ?? []).map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            min={0}
            max={100}
            value={row.pct}
            style={{ maxWidth: 80 }}
            onChange={(e) => update(i, { pct: Number(e.target.value) || 0 })}
          />
          <span className="muted">%</span>
          <button type="button" className="btn xs danger" style={{ marginLeft: 'auto' }} onClick={() => remove(i)}>
            삭제
          </button>
        </div>
      ))}
      <button type="button" className="addbtn" onClick={add}>
        + 질환 추가
      </button>
    </div>
  )
}
