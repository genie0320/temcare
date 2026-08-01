import {
  CrudListPage,
  nameColumn,
  searchFilter,
  statusColumn,
  statusFilter,
  textColumn,
  weaknessFilter,
} from '../components/CrudListPage'
import type { TemTypeListItem } from '../types/temType'

export function TemTypeListPage() {
  return (
    <CrudListPage<TemTypeListItem>
      title="64유형 마스터"
      description="64개 체질을 관리한다. 각 체질에 약점 태그를 배정하고, 노출할 콘텐츠를 큐레이션한다."
      resource="tem-types"
      queryKey="tem-types"
      newLabel="+ 새 체질"
      emptyLabel="등록된 체질이 없다."
      filters={[searchFilter('체질명·코드·별명 검색'), weaknessFilter(), statusFilter()]}
      columns={[
        nameColumn('체질', (t) => t.name),
        // 태그가 없는 체질은 '무결형'으로 표시한다 — 다른 목록의 '—'와 다르다.
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
        textColumn('nickname', '별명', (t) => t.nickname),
        statusColumn(),
      ]}
    />
  )
}
