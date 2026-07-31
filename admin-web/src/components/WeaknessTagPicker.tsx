import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import type { WeaknessListItem } from '../types/weakness'

interface WeaknessTagPickerProps {
  selectedIds: string[]
  onChange: (ids: string[]) => void
}

// docs/05_screen_conventions.md §D 실피커의 단순 버전 — 약점은 10개뿐이라 모달 없이 칩 토글로 충분하다.
export function WeaknessTagPicker({ selectedIds, onChange }: WeaknessTagPickerProps) {
  const { data } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  function toggle(id: string) {
    onChange(selectedIds.includes(id) ? selectedIds.filter((x) => x !== id) : [...selectedIds, id])
  }

  return (
    <div className="chips">
      {(data ?? []).map((w) => (
        <button
          key={w.id}
          type="button"
          className={`chip ${w.wtype === 'IDEA' ? 'idea' : ''} ${selectedIds.includes(w.id) ? '' : 'off'}`}
          onClick={() => toggle(w.id)}
        >
          {w.name}
        </button>
      ))}
    </div>
  )
}
