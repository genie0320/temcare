import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { FoodListItem } from '../types/food'
import type { WeaknessListItem } from '../types/weakness'

export function FoodListPage() {
  const [search, setSearch] = useState('')
  const [polarity, setPolarity] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['foods', search, polarity, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (polarity) params.set('polarity', polarity)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<FoodListItem[]>(`/content/foods/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<FoodListItem>[] = [
    {
      key: 'polarity',
      label: '극성',
      width: '90px',
      render: (f) => <span className={`pill ${f.polarity === '권장' ? 'a' : 'c'}`}>{f.polarity}</span>,
    },
    {
      key: 'foods',
      label: '식품',
      render: (f) => (
        <>
          <span className="name">{f.foods || '—'}</span> <span className="muted">{f.id}</span>
        </>
      ),
    },
    {
      key: 'component',
      label: '핵심성분',
      render: (f) => <span className="muted">{f.component || '—'}</span>,
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (f) =>
        f.weakness_names.length ? (
          <div className="chips">
            {f.weakness_names.map((name) => (
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
      render: (f) => <StatusBadge status={f.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="식품군 마스터"
        description="식품을 권장/제한 극성으로 관리한다. 핵심성분은 영양소 → 식품군 스토리의 연결 고리다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/foods/new')}>
            + 새 식품군
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="식품·핵심성분 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="selectbox" value={polarity} onChange={(e) => setPolarity(e.target.value)}>
            <option value="">극성 전체</option>
            <option value="권장">권장</option>
            <option value="제한">제한</option>
          </select>
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
            rowKey={(f) => f.id}
            onRowClick={(f) => navigate(`/content/foods/${f.id}`)}
            emptyLabel="등록된 식품군이 없다."
          />
        )}
      </div>
    </>
  )
}
