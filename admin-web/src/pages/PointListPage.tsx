import {
  CrudListPage,
  searchFilter,
  statusColumn,
  statusFilter,
  textColumn,
  weaknessChipsColumn,
  weaknessFilter,
} from '../components/CrudListPage'
import type { PointListItem } from '../types/point'

export function PointListPage() {
  return (
    <CrudListPage<PointListItem>
      title="혈자리 마스터"
      description="지압·마사지 관리법에서 참조하는 혈자리를 관리한다."
      resource="points"
      queryKey="points"
      newLabel="+ 새 혈자리"
      emptyLabel="등록된 혈자리가 없다."
      filters={[searchFilter('혈자리·한자·설명 검색'), weaknessFilter(), statusFilter()]}
      columns={[
        // 한자를 이름과 id 사이에 끼워 넣는다 — nameColumn 모양과 다르다.
        {
          key: 'name',
          label: '혈자리',
          render: (p) => (
            <>
              <span className="name">{p.name}</span> {p.hanja && <span className="muted">{p.hanja}</span>}{' '}
              <span className="muted">{p.id}</span>
            </>
          ),
        },
        textColumn('description', '설명', (p) => p.description),
        weaknessChipsColumn(),
        statusColumn(),
      ]}
    />
  )
}
