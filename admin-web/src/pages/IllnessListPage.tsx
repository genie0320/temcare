import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { IllnessListItem } from '../types/illness'
import type { WeaknessListItem } from '../types/weakness'

export function IllnessListPage() {
  const [search, setSearch] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['illnesses', search, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<IllnessListItem[]>(`/content/illnesses/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<IllnessListItem>[] = [
    {
      key: 'name',
      label: '예측질환',
      render: (i) => (
        <>
          <span className="name">{i.name}</span> <span className="muted">{i.id}</span>
        </>
      ),
    },
    {
      key: 'description',
      label: '설명',
      render: (i) => <span className="muted">{i.description || '—'}</span>,
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (i) =>
        i.weakness_names.length ? (
          <div className="chips">
            {i.weakness_names.map((name) => (
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
      render: (i) => <StatusBadge status={i.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="예측질환 마스터"
        description="약점 태그가 겹치는 체질 상세화면에서 발병율과 함께 노출되는 예측질환을 관리한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/illnesses/new')}>
            + 새 예측질환
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="예측질환·설명 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
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
            rowKey={(i) => i.id}
            onRowClick={(i) => navigate(`/content/illnesses/${i.id}`)}
            emptyLabel="등록된 예측질환이 없다."
          />
        )}
      </div>
    </>
  )
}
