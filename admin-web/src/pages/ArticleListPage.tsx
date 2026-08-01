import {
  CrudListPage,
  nameColumn,
  searchFilter,
  statusColumn,
  statusFilter,
  weaknessChipsColumn,
  weaknessFilter,
} from '../components/CrudListPage'
import type { ArticleKind, ArticleListItem } from '../types/article'

const KINDS: ArticleKind[] = ['식이', '지압·마사지', '생활', '뜸']

function kindPillTone(kind: ArticleKind) {
  if (kind === '식이') return 'a'
  if (kind === '생활') return 'c'
  return 'b'
}

export function ArticleListPage() {
  return (
    <CrudListPage<ArticleListItem>
      title="요법관리 마스터"
      description="유형(식이·지압마사지·생활·뜸)과 약점 태그로 체질 결과화면에 자동 노출되는 관리법을 관리한다."
      resource="articles"
      queryKey="articles"
      newLabel="+ 새 관리법"
      emptyLabel="등록된 관리법이 없다."
      filters={[
        searchFilter('관리법·제목 검색'),
        { kind: 'select', key: 'kind', allLabel: '유형 전체', options: KINDS },
        weaknessFilter(),
        statusFilter(),
      ]}
      columns={[
        // 유형별로 알약 색이 갈린다 — 이 목록에만 있는 열.
        {
          key: 'kind',
          label: '유형',
          width: '110px',
          render: (a) => <span className={`pill ${kindPillTone(a.kind)}`}>{a.kind}</span>,
        },
        nameColumn('항목명', (a) => a.title),
        weaknessChipsColumn(),
        statusColumn(),
      ]}
    />
  )
}
