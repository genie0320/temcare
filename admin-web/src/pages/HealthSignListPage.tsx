import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { HealthSignListItem } from '../types/healthSign'
import type { WeaknessListItem } from '../types/weakness'

export function HealthSignListPage() {
  const [search, setSearch] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['health-signs', search, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<HealthSignListItem[]>(`/content/health-signs/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<HealthSignListItem>[] = [
    {
      key: 'name',
      label: '건강신호',
      render: (s) => (
        <>
          <span className="name">{s.name}</span> <span className="muted">{s.id}</span>
        </>
      ),
    },
    {
      key: 'note',
      label: '설명',
      render: (s) => <span className="muted">{s.note || '—'}</span>,
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (s) =>
        s.weakness_names.length ? (
          <div className="chips">
            {s.weakness_names.map((name) => (
              <span key={name} className="chip">
                {name}
              </span>
            ))}
          </div>
        ) : (
          <span className="muted">—</span>
        ),
    },
    {
      key: 'status',
      label: '상태',
      width: '80px',
      render: (s) => <StatusBadge status={s.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="건강신호 마스터"
        description="약점 태그가 겹치는 체질 결과화면에 아코디언으로 노출되는 건강신호를 관리한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/health-signs/new')}>
            + 새 건강신호
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="건강신호·설명 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="selectbox" value={weakness} onChange={(e) => setWeakness(e.target.value)}>
            <option value="">약점 전체</option>
            {(weaknesses ?? []).map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
          <select className="selectbox" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">상태 전체</option>
            <option value="게시">게시</option>
            <option value="초안">초안</option>
            <option value="숨김">숨김</option>
          </select>
        </div>
        {isPending ? (
          <div className="empty">불러오는 중…</div>
        ) : isError ? (
          <div className="empty">목록을 불러오지 못했다.</div>
        ) : (
          <DataTable
            columns={columns}
            rows={data ?? []}
            rowKey={(s) => s.id}
            onRowClick={(s) => navigate(`/content/health-signs/${s.id}`)}
            emptyLabel="등록된 건강신호가 없다."
          />
        )}
      </div>
    </>
  )
}
