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
import type { IllnessListItem } from '../types/illness'

export function IllnessListPage() {
  return (
    <CrudListPage<IllnessListItem>
      title="예측질환 마스터"
      description="약점 태그가 겹치는 체질 상세화면에서 발병율과 함께 노출되는 예측질환을 관리한다."
      resource="illnesses"
      queryKey="illnesses"
      newLabel="+ 새 예측질환"
      emptyLabel="등록된 예측질환이 없다."
      filters={[searchFilter('예측질환·설명 검색'), weaknessFilter(), statusFilter()]}
      columns={[
        nameColumn('예측질환', (i) => i.name),
        textColumn('description', '설명', (i) => i.description),
        weaknessChipsColumn(),
        statusColumn(),
      ]}
    />
  )
}
