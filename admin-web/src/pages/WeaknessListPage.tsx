import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { WeaknessListItem } from '../types/weakness'

export function WeaknessListPage() {
  const [search, setSearch] = useState('')
  const [wtype, setWtype] = useState('')
  const navigate = useNavigate()

  const { data, isPending, isError } = useQuery({
    queryKey: ['weaknesses', search, wtype],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (wtype) params.set('wtype', wtype)
      const qs = params.toString()
      return apiGet<WeaknessListItem[]>(`/content/weaknesses/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<WeaknessListItem>[] = [
    {
      key: 'name',
      label: '항목명',
      render: (w) => <span className="name">{w.name}</span>,
    },
    {
      key: 'wtype',
      label: '타입',
      render: (w) => <span className={`pill ${w.wtype === 'IDEA' ? 'b' : 'a'}`}>{w.wtype}</span>,
    },
    {
      key: 'catchphrase',
      label: '캐치프레이즈',
      render: (w) => <span className="muted">{w.catchphrase || '—'}</span>,
    },
    {
      key: 'linked_content_count',
      label: '연결 콘텐츠수',
      render: (w) => <span className="muted">{w.linked_content_count}건</span>,
    },
    {
      key: 'status',
      label: '상태',
      width: '80px',
      render: (w) => <StatusBadge status={w.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="약점 / IDEA 마스터"
        description="10개 약점(6 조합형 + 4 IDEA)과 무결형. 타입·격언을 관리한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/weaknesses/new')}>
            + 새 약점
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="약점명·ID 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="selectbox" value={wtype} onChange={(e) => setWtype(e.target.value)}>
            <option value="">타입 전체</option>
            <option value="약점">약점</option>
            <option value="IDEA">IDEA</option>
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
            rowKey={(w) => w.id}
            onRowClick={(w) => navigate(`/content/weaknesses/${w.id}`)}
            emptyLabel="등록된 약점이 없다."
          />
        )}
      </div>
    </>
  )
}
