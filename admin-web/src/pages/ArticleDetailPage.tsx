import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, SegToggle, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { ReferencePickList } from '../components/ReferencePickList'
import { RichTextEditor } from '../components/RichTextEditor'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import { useCrudDetail } from '../hooks/useCrudDetail'
import type { ArticleDetail, ArticleDraft, ArticleKind } from '../types/article'
import type { CandidateItem } from '../types/temType'
import type { FoodListItem } from '../types/food'
import type { PointListItem } from '../types/point'
import type { ProductListItem } from '../types/product'

const KINDS: ArticleKind[] = ['식이', '지압·마사지', '생활', '뜸']

const EMPTY_DRAFT: ArticleDraft = {
  kind: '식이',
  title: '',
  body: '',
  image: '',
  video: '',
  status: '게시',
  sort: 0,
  weakness_ids: [],
  food_ids: [],
  point_ids: [],
  product_ids: [],
}

export function ArticleDetailPage() {
  const crud = useCrudDetail<ArticleDraft, ArticleDetail>({
    resource: 'articles',
    queryKey: 'article',
    listQueryKey: 'articles',
    basePath: '/content/articles',
    empty: EMPTY_DRAFT,
    required: [
      { field: 'kind', message: '유형은 필수다.' },
      { field: 'title', message: '항목명은 필수다.' },
      { field: 'weakness_ids', message: '연결 약점은 필수다. 없으면 체질 결과화면에 자동 노출되지 않는다.' },
    ],
    deleteConfirm: '이 관리법을 삭제할까? 약점·참고정보 연결도 함께 삭제된다.',
  })
  const { draft, set, data, isNew } = crud

  const { data: foods } = useQuery({
    queryKey: ['foods-all'],
    queryFn: () => apiGet<FoodListItem[]>('/content/foods/'),
  })
  const { data: points } = useQuery({
    queryKey: ['points-all'],
    queryFn: () => apiGet<PointListItem[]>('/content/points/'),
  })
  const { data: products } = useQuery({
    queryKey: ['products-all'],
    queryFn: () => apiGet<ProductListItem[]>('/content/products/'),
  })

  const foodCandidates: CandidateItem[] = (foods ?? []).map((f) => ({
    id: f.id,
    name: f.foods,
    sub: f.component,
    polarity: f.polarity,
  }))
  const pointCandidates: CandidateItem[] = (points ?? []).map((p) => ({ id: p.id, name: p.name, sub: p.hanja }))
  const productCandidates: CandidateItem[] = (products ?? []).map((p) => ({ id: p.id, name: p.name, sub: '' }))

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '관리법 상세 · 새 관리법' : `관리법 상세 · ${data?.title ?? ''}`}
      backTo="/content/articles"
    >
      <Card title="기본정보">
        <div className="form-grid">
          <FormRow label="유형" required>
            <SegToggle value={draft.kind} options={KINDS} onChange={(v) => set('kind', v)} />
          </FormRow>
          <FormRow label="항목명" required>
            <TextInput value={draft.title} onChange={(v) => set('title', v)} placeholder="예: 위장마사지 (명치 → 윗배)" />
          </FormRow>
          <FormRow label="설명">
            <RichTextEditor value={draft.body} onChange={(v) => set('body', v)} />
          </FormRow>
          <FormRow label="대표 이미지">
            <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_024" />
          </FormRow>
          <FormRow label="연결 약점" required>
            <WeaknessTagPicker selectedIds={draft.weakness_ids} onChange={(ids) => set('weakness_ids', ids)} />
          </FormRow>
        </div>
      </Card>

      <Card title="참고정보" sub="영상·마스터 연결">
        <div className="form-grid">
          <FormRow label="식품군">
            <ReferencePickList label="식품군" ids={draft.food_ids} candidates={foodCandidates} onChange={(ids) => set('food_ids', ids)} />
          </FormRow>
          <FormRow label="혈자리">
            <ReferencePickList label="혈자리" ids={draft.point_ids} candidates={pointCandidates} onChange={(ids) => set('point_ids', ids)} />
          </FormRow>
          <FormRow label="제품">
            <ReferencePickList label="제품" ids={draft.product_ids} candidates={productCandidates} onChange={(ids) => set('product_ids', ids)} />
          </FormRow>
          <FormRow label="관련 영상 URL">
            <TextInput value={draft.video} onChange={(v) => set('video', v)} placeholder="https://..." />
            <div className="hint">유튜브 등 시연 영상 링크(선택).</div>
          </FormRow>
        </div>
      </Card>
    </CrudDetailPage>
  )
}
