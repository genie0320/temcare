import { useNavigate } from 'react-router'
import { PageHead } from '../components/PageHead'
import { StatusBadge } from '../components/StatusBadge'
import { useCrudList } from '../hooks/useCrudList'
import type { LifeArticleCategory, LifeArticleListItem } from '../types/lifeArticle'

const CATEGORIES: LifeArticleCategory[] = ['체온', '먹고싸고', '멘탈', '체질이야기']

function categoryPillTone(category: LifeArticleCategory) {
  if (category === '체온') return 'a'
  if (category === '먹고싸고') return 'c'
  if (category === '멘탈') return 'b'
  return 'd'
}

// 뉴스피드형 목록 — 다른 9개 마스터의 DataTable과 달리 큰 이미지 카드 그리드다.
// 데이터 조회·필터 상태는 useCrudList를 그대로 쓰고, 렌더링만 새로 짠다.
export function LifeArticleListPage() {
  const navigate = useNavigate()

  const { rows, isPending, isError, filters, setFilter } = useCrudList<LifeArticleListItem>({
    resource: 'life-articles',
    queryKey: 'life-articles',
    filterKeys: ['search', 'category', 'status'],
  })

  return (
    <>
      <PageHead
        title="템라이프 마스터"
        description="이미지 중심 뉴스피드 콘텐츠를 카테고리별로 관리한다. 다른 템콘텐츠·관련 기사는 상세에서 연결한다."
        actions={
          <button className="btn primary" onClick={() => navigate('/content/life-articles/new')}>
            + 새 템라이프 글
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <div className="search">
            <input
              placeholder="제목·본문 검색"
              value={filters.search ?? ''}
              onChange={(e) => setFilter('search', e.target.value)}
            />
          </div>
          <select className="selectbox" value={filters.category ?? ''} onChange={(e) => setFilter('category', e.target.value)}>
            <option value="">카테고리 전체</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select className="selectbox" value={filters.status ?? ''} onChange={(e) => setFilter('status', e.target.value)}>
            <option value="">상태 전체</option>
            <option value="게시">게시</option>
            <option value="초안">초안</option>
            <option value="숨김">숨김</option>
          </select>
        </div>
        {isPending ? (
          <div className="empty">불러오는 중…</div>
        ) : isError ? (
          <div className="empty">목록을 불러오지 못했다.</div>
        ) : rows.length === 0 ? (
          <div className="empty">등록된 템라이프 글이 없다.</div>
        ) : (
          <div className="life-grid">
            {rows.map((row) => (
              <button
                key={row.id}
                type="button"
                className="life-card"
                onClick={() => navigate(`/content/life-articles/${row.id}`)}
              >
                <div className="life-card-img">
                  {row.image ? <img src={row.image} alt="" /> : <span className="ph">🖼️</span>}
                </div>
                <div className="life-card-body">
                  <span className={`pill ${categoryPillTone(row.category)}`}>{row.category}</span>
                  <div className="life-card-title">{row.title}</div>
                  <div className="life-card-foot">
                    <span className="muted">{row.id}</span>
                    <StatusBadge status={row.status} />
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
