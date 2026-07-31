import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { NutrientListItem } from '../types/nutrient'
import type { WeaknessListItem } from '../types/weakness'

export function NutrientListPage() {
  const [search, setSearch] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['nutrients', search, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<NutrientListItem[]>(`/content/nutrients/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<NutrientListItem>[] = [
    {
      key: 'name',
      label: '영양소',
      render: (n) => (
        <>
          <span className="name">{n.name}</span> <span className="muted">{n.id}</span>
        </>
      ),
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (n) =>
        n.weakness_names.length ? (
          <div className="chips">
            {n.weakness_names.map((name) => (
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
      key: 'card_count',
      label: '카드수',
      width: '90px',
      render: (n) => <span className="muted">{n.card_count}개</span>,
    },
    {
      key: 'status',
      label: '상태',
      width: '80px',
      render: (n) => <StatusBadge status={n.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="영양소 마스터"
        description="영양소를 한 번 등록하면 약점 태그로 여러 체질에 재사용된다. 같은 영양소도 약점별 관점(카드)이 다르다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/nutrients/new')}>
            + 새 영양소
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="영양소명·ID·관점 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
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
            rowKey={(n) => n.id}
            onRowClick={(n) => navigate(`/content/nutrients/${n.id}`)}
            emptyLabel="등록된 영양소가 없다."
          />
        )}
      </div>
    </>
  )
}
