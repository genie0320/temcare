import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { apiDelete, apiGet, apiPatch, apiPost } from '../api/client'
import { Card, DetailLayout } from '../components/DetailLayout'
import { FormRow, SegToggle, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { MetaPanel } from '../components/MetaPanel'
import { PageHead } from '../components/PageHead'
import { PublishBox } from '../components/PublishBox'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import type { FoodDetail, FoodDraft, FoodPolarity } from '../types/food'

const EMPTY_DRAFT: FoodDraft = {
  polarity: '권장',
  foods: '',
  component: '',
  description: '',
  image: '',
  status: '게시',
  sort: 0,
  weakness_ids: [],
}

export function FoodDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['food', id],
    queryFn: () => apiGet<FoodDetail>(`/content/foods/${id}/`),
    enabled: !isNew,
  })

  const { data: componentOptions } = useQuery({
    queryKey: ['food-components'],
    queryFn: () => apiGet<string[]>('/content/food-components/'),
  })

  const [draft, setDraft] = useState<FoodDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof FoodDraft>(key: K, value: FoodDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.foods.trim()) {
      setErrorMsg('식품(항목명)은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<FoodDetail>('/content/foods/', draft)
        : await apiPatch<FoodDetail>(`/content/foods/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['foods'] })
      await queryClient.invalidateQueries({ queryKey: ['food'] })
      await queryClient.invalidateQueries({ queryKey: ['food-components'] })
      navigate(`/content/foods/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 식품군을 삭제할까? 약점 태그 연결도 함께 사라진다.')) return
    await apiDelete(`/content/foods/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['foods'] })
    navigate('/content/foods')
  }

  return (
    <>
      <PageHead title={isNew ? '식품군 상세 · 새 식품군' : `식품군 상세 · ${data?.foods ?? ''}`} backTo="/content/foods" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="극성(타입)" required>
                  <SegToggle value={draft.polarity} options={['권장', '제한'] as FoodPolarity[]} onChange={(v) => set('polarity', v)} />
                </FormRow>
                <FormRow label="식품" required>
                  <TextArea value={draft.foods} onChange={(v) => set('foods', v)} placeholder="예: 시금치·케일·브로콜리·오이·토마토" />
                </FormRow>
                <FormRow label="핵심성분">
                  <TextInput
                    value={draft.component}
                    onChange={(v) => set('component', v)}
                    placeholder="예: 칼륨 (선택)"
                    listOptions={componentOptions}
                  />
                  <div className="hint">자유 입력이다. 앞서 쓴 값이 있으면 후보로 떠서 표기를 통일할 수 있다.</div>
                </FormRow>
                <FormRow label="설명" required>
                  <TextArea value={draft.description} onChange={(v) => set('description', v)} placeholder="이 식품군이 어떤 도움을 주는지" />
                </FormRow>
                <FormRow label="대표 이미지">
                  <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_025" />
                </FormRow>
                <FormRow label="관련 약점" required>
                  <WeaknessTagPicker selectedIds={draft.weakness_ids} onChange={(ids) => set('weakness_ids', ids)} />
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
