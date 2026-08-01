import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { PointListItem } from '../types/point'
import type { WeaknessListItem } from '../types/weakness'

export function PointListPage() {
  const [search, setSearch] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['points', search, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<PointListItem[]>(`/content/points/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<PointListItem>[] = [
    {
      key: 'name',
      label: '혈자리',
      render: (p) => (
        <>
          <span className="name">{p.name}</span> {p.hanja && <span className="muted">{p.hanja}</span>}{' '}
          <span className="muted">{p.id}</span>
        </>
      ),
    },
    {
      key: 'description',
      label: '설명',
      render: (p) => <span className="muted">{p.description || '—'}</span>,
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (p) =>
        p.weakness_names.length ? (
          <div className="chips">
            {p.weakness_names.map((name) => (
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
      render: (p) => <StatusBadge status={p.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="혈자리 마스터"
        description="지압·마사지 관리법에서 참조하는 혈자리를 관리한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/points/new')}>
            + 새 혈자리
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="혈자리·한자·설명 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
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
            rowKey={(p) => p.id}
            onRowClick={(p) => navigate(`/content/points/${p.id}`)}
            emptyLabel="등록된 혈자리가 없다."
          />
        )}
      </div>
    </>
  )
}
