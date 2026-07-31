import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { HerbListItem } from '../types/herb'
import type { WeaknessListItem } from '../types/weakness'

export function HerbListPage() {
  const [search, setSearch] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['herbs', search, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<HerbListItem[]>(`/content/herbs/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<HerbListItem>[] = [
    {
      key: 'name',
      label: '약재',
      render: (h) => (
        <>
          <span className="name">{h.name}</span> {h.hanja && <span className="muted">{h.hanja}</span>}{' '}
          <span className="muted">{h.id}</span>
        </>
      ),
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (h) =>
        h.weakness_names.length ? (
          <div className="chips">
            {h.weakness_names.map((name) => (
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
      render: (h) => <span className="muted">{h.card_count}개</span>,
    },
    {
      key: 'status',
      label: '상태',
      width: '80px',
      render: (h) => <StatusBadge status={h.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="약재 마스터"
        description="인생처방(약재)을 등록·수정·삭제한다. 영양소와 동일 패턴 — 약재 + 약점별 효능기전 카드."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/herbs/new')}>
            + 새 약재
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="약재명·한자·효능 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
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
            rowKey={(h) => h.id}
            onRowClick={(h) => navigate(`/content/herbs/${h.id}`)}
            emptyLabel="등록된 약재가 없다."
          />
        )}
      </div>
    </>
  )
}
