import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { ArticleKind, ArticleListItem } from '../types/article'
import type { WeaknessListItem } from '../types/weakness'

const KINDS: ArticleKind[] = ['식이', '지압·마사지', '생활', '뜸']

function kindPillTone(kind: ArticleKind) {
  if (kind === '식이') return 'a'
  if (kind === '생활') return 'c'
  return 'b'
}

export function ArticleListPage() {
  const [search, setSearch] = useState('')
  const [kind, setKind] = useState('')
  const [weakness, setWeakness] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data: weaknesses } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['articles', search, kind, weakness, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (kind) params.set('kind', kind)
      if (weakness) params.set('weakness', weakness)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<ArticleListItem[]>(`/content/articles/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<ArticleListItem>[] = [
    {
      key: 'kind',
      label: '유형',
      width: '110px',
      render: (a) => <span className={`pill ${kindPillTone(a.kind)}`}>{a.kind}</span>,
    },
    {
      key: 'title',
      label: '항목명',
      render: (a) => (
        <>
          <span className="name">{a.title}</span> <span className="muted">{a.id}</span>
        </>
      ),
    },
    {
      key: 'weakness_names',
      label: '약점 태그',
      render: (a) =>
        a.weakness_names.length ? (
          <div className="chips">
            {a.weakness_names.map((name) => (
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
      render: (a) => <StatusBadge status={a.status} />,
    },
  ]

  return (
    <>
      <PageHead
        title="요법관리 마스터"
        description="유형(식이·지압마사지·생활·뜸)과 약점 태그로 체질 결과화면에 자동 노출되는 관리법을 관리한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/articles/new')}>
            + 새 관리법
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="관리법·제목 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="selectbox" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="">유형 전체</option>
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
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
            rowKey={(a) => a.id}
            onRowClick={(a) => navigate(`/content/articles/${a.id}`)}
            emptyLabel="등록된 관리법이 없다."
          />
        )}
      </div>
    </>
  )
}
