import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { TemTypeListItem } from '../types/temType'
import type { WeaknessListItem } from '../types/weakness'

export function TemTypeListPage() {
  const [search, setSearch] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['tem-types', search, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<TemTypeListItem[]>(`/content/tem-types/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<TemTypeListItem>[] = [
    {
      key: 'name',
      label: '체질',
      render: (t) => (
        <>
          <span className="name">{t.name}</span> <span className="muted">{t.id}</span>
        </>
      ),
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (t) =>
        t.weakness_names.length ? (
          <div className="chips">
            {t.weakness_names.map((n) => (
              <span key={n} className="chip">
                {n}
              </span>
            ))}
          </div>
        ) : (
          <span className="chip off">무결형</span>
        ),
    },
    {
      key: 'nickname',
      label: '별명',
      render: (t) => <span className="muted">{t.nickname || '—'}</span>,
    },
    {
      key: 'status',
      label: '상태',
      render: (t) => <StatusBadge status={t.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="64유형 마스터"
        description="64개 체질을 관리한다. 각 체질에 약점 태그를 배정하고, 노출할 콘텐츠를 큐레이션한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/tem-types/new')}>
            + 새 체질
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="체질명·코드·별명 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
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
            rowKey={(t) => t.id}
            onRowClick={(t) => navigate(`/content/tem-types/${t.id}`)}
            emptyLabel="등록된 체질이 없다."
          />
        )}
      </div>
    </>
  )
}
