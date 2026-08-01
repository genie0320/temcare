import {
  CrudListPage,
  nameColumn,
  searchFilter,
  statusColumn,
  statusFilter,
} from '../components/CrudListPage'
import type { ProductListItem } from '../types/product'

export function ProductListPage() {
  return (
    <CrudListPage<ProductListItem>
      title="제품 마스터"
      description="요법관리의 참고정보에서 연결해 고객 화면에 추천으로 노출할 수 있는 제품을 관리한다."
      resource="products"
      queryKey="products"
      newLabel="+ 새 제품"
      emptyLabel="등록된 제품이 없다."
      filters={[searchFilter('상품명·설명·URL 검색'), statusFilter()]}
      columns={[
        nameColumn('상품', (p) => p.name),
        // 외부 링크. 행 클릭(상세 이동)과 겹치지 않도록 클릭을 멈춘다.
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
        statusColumn(),
      ]}
    />
  )
}
