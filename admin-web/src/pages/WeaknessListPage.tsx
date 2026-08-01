import { CrudListPage, searchFilter, statusColumn, textColumn } from '../components/CrudListPage'
import type { WeaknessListItem } from '../types/weakness'

export function WeaknessListPage() {
  return (
    <CrudListPage<WeaknessListItem>
      title="약점 / IDEA 마스터"
      description="10개 약점(6 조합형 + 4 IDEA)과 무결형. 타입·격언을 관리한다."
      resource="weaknesses"
      queryKey="weaknesses"
      newLabel="+ 새 약점"
      emptyLabel="등록된 약점이 없다."
      filters={[
        searchFilter('약점명·ID 검색'),
        { kind: 'select', key: 'wtype', allLabel: '타입 전체', options: ['약점', 'IDEA'] },
      ]}
      columns={[
        // 다른 목록과 달리 id를 함께 보여주지 않는다 — nameColumn을 쓸 수 없다.
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
        textColumn('catchphrase', '캐치프레이즈', (w) => w.catchphrase),
        textColumn('linked_content_count', '연결 콘텐츠수', (w) => `${w.linked_content_count}건`),
        statusColumn(),
      ]}
    />
  )
}
