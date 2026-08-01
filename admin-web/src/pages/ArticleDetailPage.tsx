import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { apiDelete, apiGet, apiPatch, apiPost } from '../api/client'
import { Card, DetailLayout } from '../components/DetailLayout'
import { FormRow, SegToggle, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { MetaPanel } from '../components/MetaPanel'
import { PageHead } from '../components/PageHead'
import { PublishBox } from '../components/PublishBox'
import { ReferencePickList } from '../components/ReferencePickList'
import { RichTextEditor } from '../components/RichTextEditor'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
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
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['article', id],
    queryFn: () => apiGet<ArticleDetail>(`/content/articles/${id}/`),
    enabled: !isNew,
  })

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

  const [draft, setDraft] = useState<ArticleDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof ArticleDraft>(key: K, value: ArticleDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.title.trim()) {
      setErrorMsg('항목명은 필수다.')
      return
    }
    if (draft.weakness_ids.length === 0) {
      setErrorMsg('연결 약점은 필수다. 없으면 체질 결과화면에 자동 노출되지 않는다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<ArticleDetail>('/content/articles/', draft)
        : await apiPatch<ArticleDetail>(`/content/articles/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['articles'] })
      await queryClient.invalidateQueries({ queryKey: ['article'] })
      navigate(`/content/articles/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 관리법을 삭제할까? 약점·참고정보 연결도 함께 삭제된다.')) return
    await apiDelete(`/content/articles/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['articles'] })
    navigate('/content/articles')
  }

  return (
    <>
      <PageHead title={isNew ? '관리법 상세 · 새 관리법' : `관리법 상세 · ${data?.title ?? ''}`} backTo="/content/articles" />
      <DetailLayout
        main={
          <>
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

            {errorMsg && (
              <div className="note warn">
                <span className="i">⚠</span> {errorMsg}
              </div>
            )}
          </>
        }
        side={
          <>
            <PublishBox
              status={draft.status}
              onStatusChange={(s) => set('status', s)}
              onSave={handleSave}
              onDelete={isNew ? undefined : handleDelete}
              saving={saving}
              isNew={isNew}
            />
            <MetaPanel
              id={data?.id ?? ''}
              createdAt={data?.created_at ?? ''}
              updatedAt={data?.updated_at ?? ''}
              updatedBy={data?.updated_by ?? ''}
            />
          </>
        }
      />
    </>
  )
}
