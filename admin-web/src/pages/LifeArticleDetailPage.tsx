import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, SegToggle, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { ReferencePickList } from '../components/ReferencePickList'
import { RichTextEditor } from '../components/RichTextEditor'
import { useCrudDetail } from '../hooks/useCrudDetail'
import type { ArticleListItem } from '../types/article'
import type { FoodListItem } from '../types/food'
import type { HealthSignListItem } from '../types/healthSign'
import type { HerbListItem } from '../types/herb'
import type { IllnessListItem } from '../types/illness'
import type { LifeArticleCategory, LifeArticleDetail, LifeArticleDraft, LifeArticleListItem } from '../types/lifeArticle'
import type { NutrientListItem } from '../types/nutrient'
import type { PointListItem } from '../types/point'
import type { ProductListItem } from '../types/product'
import type { CandidateItem } from '../types/temType'

const CATEGORIES: LifeArticleCategory[] = ['체온', '먹고싸고', '멘탈', '체질이야기']

const EMPTY_DRAFT: LifeArticleDraft = {
  category: '체온',
  title: '',
  body: '',
  image: '',
  video: '',
  status: '게시',
  sort: 0,
  nutrient_ids: [],
  herb_ids: [],
  food_ids: [],
  point_ids: [],
  health_sign_ids: [],
  illness_ids: [],
  product_ids: [],
  article_ids: [],
  related_article_ids: [],
}

function useAllContent<T>(resource: string) {
  return useQuery({
    queryKey: [`${resource}-all`],
    queryFn: () => apiGet<T[]>(`/content/${resource}/`),
  }).data
}

export function LifeArticleDetailPage() {
  const crud = useCrudDetail<LifeArticleDraft, LifeArticleDetail>({
    resource: 'life-articles',
    queryKey: 'life-article',
    listQueryKey: 'life-articles',
    basePath: '/content/life-articles',
    empty: EMPTY_DRAFT,
    required: [
      { field: 'title', message: '항목명은 필수다.' },
      { field: 'category', message: '카테고리는 필수다.' },
    ],
    deleteConfirm: '이 템라이프 글을 삭제할까? 다른 콘텐츠·관련 기사 연결도 함께 삭제된다.',
  })
  const { draft, set, data, isNew } = crud

  const nutrients = useAllContent<NutrientListItem>('nutrients')
  const herbs = useAllContent<HerbListItem>('herbs')
  const foods = useAllContent<FoodListItem>('foods')
  const points = useAllContent<PointListItem>('points')
  const healthSigns = useAllContent<HealthSignListItem>('health-signs')
  const illnesses = useAllContent<IllnessListItem>('illnesses')
  const products = useAllContent<ProductListItem>('products')
  const articles = useAllContent<ArticleListItem>('articles')
  const lifeArticles = useAllContent<LifeArticleListItem>('life-articles')

  const nutrientCandidates: CandidateItem[] = (nutrients ?? []).map((n) => ({ id: n.id, name: n.name, sub: '' }))
  const herbCandidates: CandidateItem[] = (herbs ?? []).map((h) => ({ id: h.id, name: h.name, sub: h.hanja }))
  const foodCandidates: CandidateItem[] = (foods ?? []).map((f) => ({
    id: f.id,
    name: f.foods,
    sub: f.component,
    polarity: f.polarity,
  }))
  const pointCandidates: CandidateItem[] = (points ?? []).map((p) => ({ id: p.id, name: p.name, sub: p.hanja }))
  const healthSignCandidates: CandidateItem[] = (healthSigns ?? []).map((s) => ({ id: s.id, name: s.name, sub: '' }))
  const illnessCandidates: CandidateItem[] = (illnesses ?? []).map((i) => ({ id: i.id, name: i.name, sub: '' }))
  const productCandidates: CandidateItem[] = (products ?? []).map((p) => ({ id: p.id, name: p.name, sub: '' }))
  const articleCandidates: CandidateItem[] = (articles ?? []).map((a) => ({ id: a.id, name: a.title, sub: a.kind }))
  const relatedCandidates: CandidateItem[] = (lifeArticles ?? [])
    .filter((a) => a.id !== data?.id)
    .map((a) => ({ id: a.id, name: a.title, sub: a.category }))

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '템라이프 상세 · 새 글' : `템라이프 상세 · ${data?.title ?? ''}`}
      backTo="/content/life-articles"
    >
      <Card title="기본정보">
        <div className="form-grid">
          <FormRow label="카테고리" required>
            <SegToggle value={draft.category} options={CATEGORIES} onChange={(v) => set('category', v)} />
          </FormRow>
          <FormRow label="항목명" required>
            <TextInput value={draft.title} onChange={(v) => set('title', v)} placeholder="예: 찬 음료 대신 따뜻한 차 한 잔" />
          </FormRow>
          <FormRow label="본문">
            <RichTextEditor value={draft.body} onChange={(v) => set('body', v)} />
          </FormRow>
          <FormRow label="키비주얼(대표 이미지)">
            <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_009" />
          </FormRow>
          <FormRow label="관련 영상 URL">
            <TextInput value={draft.video} onChange={(v) => set('video', v)} placeholder="https://..." />
            <div className="hint">유튜브 등 시연 영상 링크(선택).</div>
          </FormRow>
        </div>
      </Card>

      <Card title="다른 템콘텐츠 연결" sub="콘텐츠 마스터 8종 전체에서 선택 가능">
        <div className="life-links-grid">
          <FormRow label="영양소">
            <ReferencePickList label="영양소" ids={draft.nutrient_ids} candidates={nutrientCandidates} onChange={(ids) => set('nutrient_ids', ids)} />
          </FormRow>
          <FormRow label="약재">
            <ReferencePickList label="약재" ids={draft.herb_ids} candidates={herbCandidates} onChange={(ids) => set('herb_ids', ids)} />
          </FormRow>
          <FormRow label="식품군">
            <ReferencePickList label="식품군" ids={draft.food_ids} candidates={foodCandidates} onChange={(ids) => set('food_ids', ids)} />
          </FormRow>
          <FormRow label="혈자리">
            <ReferencePickList label="혈자리" ids={draft.point_ids} candidates={pointCandidates} onChange={(ids) => set('point_ids', ids)} />
          </FormRow>
          <FormRow label="건강신호">
            <ReferencePickList label="건강신호" ids={draft.health_sign_ids} candidates={healthSignCandidates} onChange={(ids) => set('health_sign_ids', ids)} />
          </FormRow>
          <FormRow label="예측질환">
            <ReferencePickList label="예측질환" ids={draft.illness_ids} candidates={illnessCandidates} onChange={(ids) => set('illness_ids', ids)} />
          </FormRow>
          <FormRow label="제품">
            <ReferencePickList label="제품" ids={draft.product_ids} candidates={productCandidates} onChange={(ids) => set('product_ids', ids)} />
          </FormRow>
          <FormRow label="요법관리">
            <ReferencePickList label="요법관리" ids={draft.article_ids} candidates={articleCandidates} onChange={(ids) => set('article_ids', ids)} />
          </FormRow>
        </div>
      </Card>

      <Card title="관련 기사" sub="템라이프 글끼리의 연결">
        <div className="form-grid">
          <FormRow label="관련 기사">
            <ReferencePickList
              label="관련 기사"
              ids={draft.related_article_ids}
              candidates={relatedCandidates}
              onChange={(ids) => set('related_article_ids', ids)}
            />
          </FormRow>
        </div>
      </Card>
    </CrudDetailPage>
  )
}
