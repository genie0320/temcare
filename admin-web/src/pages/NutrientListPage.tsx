import {
  CrudListPage,
  nameColumn,
  searchFilter,
  statusColumn,
  statusFilter,
  weaknessChipsColumn,
  weaknessFilter,
} from '../components/CrudListPage'
import type { NutrientListItem } from '../types/nutrient'

export function NutrientListPage() {
  return (
    <CrudListPage<NutrientListItem>
      title="영양소 마스터"
      description="영양소를 한 번 등록하면 약점 태그로 여러 체질에 재사용된다. 같은 영양소도 약점별 관점(카드)이 다르다."
      resource="nutrients"
      queryKey="nutrients"
      newLabel="+ 새 영양소"
      emptyLabel="등록된 영양소가 없다."
      filters={[searchFilter('영양소명·ID·관점 검색'), weaknessFilter(), statusFilter()]}
      columns={[
        nameColumn('영양소', (n) => n.name),
        weaknessChipsColumn(),
        // 카드수는 폭 고정 열이라 textColumn으로 대체할 수 없다.
        {
          key: 'card_count',
          label: '카드수',
          width: '90px',
          render: (n) => <span className="muted">{n.card_count}개</span>,
        },
        statusColumn(),
      ]}
    />
  )
}
