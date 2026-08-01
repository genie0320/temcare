import {
  CrudListPage,
  searchFilter,
  statusColumn,
  statusFilter,
  weaknessChipsColumn,
  weaknessFilter,
} from '../components/CrudListPage'
import type { HerbListItem } from '../types/herb'

export function HerbListPage() {
  return (
    <CrudListPage<HerbListItem>
      title="약재 마스터"
      description="인생처방(약재)을 등록·수정·삭제한다. 영양소와 동일 패턴 — 약재 + 약점별 효능기전 카드."
      resource="herbs"
      queryKey="herbs"
      newLabel="+ 새 약재"
      emptyLabel="등록된 약재가 없다."
      filters={[searchFilter('약재명·한자·효능 검색'), weaknessFilter(), statusFilter()]}
      columns={[
        // 한자를 이름과 id 사이에 끼워 넣는다 — nameColumn 모양과 다르다.
        {
          key: 'name',
          label: '약재',
          render: (h) => (
            <>
              <span className="name">{h.name}</span> {h.hanja && <span className="muted">{h.hanja}</span>}{' '}
              <span className="muted">{h.id}</span>
            </>
          ),
        },
        weaknessChipsColumn(),
        // 카드수는 폭 고정 열이라 textColumn으로 대체할 수 없다.
        {
          key: 'card_count',
          label: '카드수',
          width: '90px',
          render: (h) => <span className="muted">{h.card_count}개</span>,
        },
        statusColumn(),
      ]}
    />
  )
}
