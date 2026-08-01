import {
  CrudListPage,
  nameColumn,
  searchFilter,
  statusColumn,
  statusFilter,
  textColumn,
  weaknessChipsColumn,
  weaknessFilter,
} from '../components/CrudListPage'
import type { FoodListItem } from '../types/food'

export function FoodListPage() {
  return (
    <CrudListPage<FoodListItem>
      title="식품군 마스터"
      description="식품을 권장/제한 극성으로 관리한다. 핵심성분은 영양소 → 식품군 스토리의 연결 고리다."
      resource="foods"
      queryKey="foods"
      newLabel="+ 새 식품군"
      emptyLabel="등록된 식품군이 없다."
      filters={[
        searchFilter('식품·핵심성분 검색'),
        { kind: 'select', key: 'polarity', allLabel: '극성 전체', options: ['권장', '제한'] },
        weaknessFilter(),
        statusFilter(),
      ]}
      columns={[
        // 극성 알약은 이 목록에만 있다.
        {
          key: 'polarity',
          label: '극성',
          width: '90px',
          render: (f) => <span className={`pill ${f.polarity === '권장' ? 'a' : 'c'}`}>{f.polarity}</span>,
        },
        nameColumn('식품', (f) => f.foods || '—'),
        textColumn('component', '핵심성분', (f) => f.component),
        weaknessChipsColumn(),
        statusColumn(),
      ]}
    />
  )
}
