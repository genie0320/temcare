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
import type { HealthSignListItem } from '../types/healthSign'

export function HealthSignListPage() {
  return (
    <CrudListPage<HealthSignListItem>
      title="건강신호 마스터"
      description="약점 태그가 겹치는 체질 결과화면에 아코디언으로 노출되는 건강신호를 관리한다."
      resource="health-signs"
      queryKey="health-signs"
      newLabel="+ 새 건강신호"
      emptyLabel="등록된 건강신호가 없다."
      filters={[searchFilter('건강신호·설명 검색'), weaknessFilter(), statusFilter()]}
      columns={[
        nameColumn('건강신호', (s) => s.name),
        textColumn('note', '설명', (s) => s.note),
        weaknessChipsColumn(),
        statusColumn(),
      ]}
    />
  )
}
