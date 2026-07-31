import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { apiDelete, apiGet, apiPatch, apiPost } from '../api/client'
import { Card, DetailLayout } from '../components/DetailLayout'
import { FormRow, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { MetaPanel } from '../components/MetaPanel'
import { PageHead } from '../components/PageHead'
import { PublishBox } from '../components/PublishBox'
import { RepeatableCards } from '../components/RepeatableCards'
import type { NutrientDetail, NutrientDraft } from '../types/nutrient'

const EMPTY_DRAFT: NutrientDraft = {
  name: '',
  image: '',
  status: '게시',
  sort: 0,
  cards: [{ perspective: '', description: '', weakness_ids: [] }],
}

export function NutrientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['nutrient', id],
    queryFn: () => apiGet<NutrientDetail>(`/content/nutrients/${id}/`),
    enabled: !isNew,
  })

  const { data: perspectiveOptions } = useQuery({
    queryKey: ['nutrient-perspectives'],
    queryFn: () => apiGet<string[]>('/content/nutrient-perspectives/'),
  })

  const [draft, setDraft] = useState<NutrientDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof NutrientDraft>(key: K, value: NutrientDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.name.trim()) {
      setErrorMsg('영양소명은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<NutrientDetail>('/content/nutrients/', draft)
        : await apiPatch<NutrientDetail>(`/content/nutrients/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['nutrients'] })
      await queryClient.invalidateQueries({ queryKey: ['nutrient'] })
      await queryClient.invalidateQueries({ queryKey: ['nutrient-perspectives'] })
      navigate(`/content/nutrients/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 영양소를 삭제할까? 관점 카드·약점 태그도 함께 사라진다.')) return
    await apiDelete(`/content/nutrients/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['nutrients'] })
    navigate('/content/nutrients')
  }

  return (
    <>
      <PageHead title={isNew ? '영양소 상세 · 새 영양소' : `영양소 상세 · ${data?.name ?? ''}`} backTo="/content/nutrients" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="영양소명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 비타민 B-complex" />
                </FormRow>
                <FormRow label="대표 이미지">
                  <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_022" />
                </FormRow>
              </div>
            </Card>

            <Card title="약점별 관점 카드" sub="같은 영양소, 다른 관점">
              <RepeatableCards
                cards={draft.cards}
                onChange={(cards) => set('cards', cards)}
                fieldLabel="개선분야(관점)"
                fieldPlaceholder="예: 대사회복"
                perspectiveOptions={perspectiveOptions}
                addLabel="+ 관점 카드 추가"
              />
              <div className="hint" style={{ marginTop: 8 }}>
                카드마다 관점(개선분야)·설명·약점 태그를 단다. 고객 화면에선 약점 태그가 겹치는 관점 카드가 노출된다.
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
