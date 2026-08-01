import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { apiGet } from '../api/client'
import { DataTable, type Column } from '../components/DataTable'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import type { ProductListItem } from '../types/product'

export function ProductListPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const { data, isPending, isError } = useQuery({
    queryKey: ['products', search, status],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (status) params.set('status', status)
      const qs = params.toString()
      return apiGet<ProductListItem[]>(`/content/products/${qs ? `?${qs}` : ''}`)
    },
  })

  const columns: Column<ProductListItem>[] = [
    {
      key: 'name',
      label: '상품',
      render: (p) => (
        <>
          <span className="name">{p.name}</span> <span className="muted">{p.id}</span>
        </>
      ),
    },
    {
      key: 'url',
      label: '연결 URL',
      render: (p) =>
        p.url ? (
          <a
            href={p.url}
            target="_blank"
            rel="noreferrer"
            className="muted"
            style={{ textDecoration: 'underline' }}
            onClick={(e) => e.stopPropagation()}
          >
            {p.url}
          </a>
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
        title="제품 마스터"
        description="요법관리의 참고정보에서 연결해 고객 화면에 추천으로 노출할 수 있는 제품을 관리한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/products/new')}>
            + 새 제품
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input placeholder="상품명·설명·URL 검색" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
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
            onRowClick={(p) => navigate(`/content/products/${p.id}`)}
            emptyLabel="등록된 제품이 없다."
          />
        )}
      </div>
    </>
  )
}
