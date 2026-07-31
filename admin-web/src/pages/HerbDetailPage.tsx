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
import { RepeatableCards, type RepeatableCardItem } from '../components/RepeatableCards'
import type { HerbCardDraft, HerbDetail, HerbDraft } from '../types/herb'

const EMPTY_DRAFT: HerbDraft = {
  name: '',
  hanja: '',
  image: '',
  status: '게시',
  sort: 0,
  cards: [{ mechanism: '', description: '', weakness_ids: [] }],
}

// RepeatableCards는 {perspective, description, weakness_ids} 모양을 쓴다(영양소가 먼저
// 그 이름으로 만들어졌다). 약재는 필드명이 mechanism이라 여기서만 얇게 맞바꾼다 —
// 공용 컴포넌트에 화면마다 다른 필드명을 넣느니 호출부에서 변환하는 편이 더 단순하다.
function toRepeatableCards(cards: HerbCardDraft[]): RepeatableCardItem[] {
  return cards.map((c) => ({ perspective: c.mechanism, description: c.description, weakness_ids: c.weakness_ids }))
}

function fromRepeatableCards(cards: RepeatableCardItem[]): HerbCardDraft[] {
  return cards.map((c) => ({ mechanism: c.perspective, description: c.description, weakness_ids: c.weakness_ids }))
}

export function HerbDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['herb', id],
    queryFn: () => apiGet<HerbDetail>(`/content/herbs/${id}/`),
    enabled: !isNew,
  })

  const { data: mechanismOptions } = useQuery({
    queryKey: ['herb-mechanisms'],
    queryFn: () => apiGet<string[]>('/content/herb-mechanisms/'),
  })

  const [draft, setDraft] = useState<HerbDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof HerbDraft>(key: K, value: HerbDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.name.trim()) {
      setErrorMsg('약재명은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<HerbDetail>('/content/herbs/', draft)
        : await apiPatch<HerbDetail>(`/content/herbs/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['herbs'] })
      await queryClient.invalidateQueries({ queryKey: ['herb'] })
      await queryClient.invalidateQueries({ queryKey: ['herb-mechanisms'] })
      navigate(`/content/herbs/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 약재를 삭제할까? 효능 카드·약점 태그도 함께 사라진다.')) return
    await apiDelete(`/content/herbs/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['herbs'] })
    navigate('/content/herbs')
  }

  return (
    <>
      <PageHead title={isNew ? '약재 상세 · 새 약재' : `약재 상세 · ${data?.name ?? ''}`} backTo="/content/herbs" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="약재명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 육계" />
                </FormRow>
                <FormRow label="한자/생약명">
                  <TextInput value={draft.hanja} onChange={(v) => set('hanja', v)} placeholder="예: 肉桂 (Cinnamomi Cortex)" />
                </FormRow>
                <FormRow label="대표 이미지">
                  <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_023" />
                </FormRow>
              </div>
            </Card>

            <Card title="약점별 효능 카드" sub="같은 약재, 다른 효능">
              <RepeatableCards
                cards={toRepeatableCards(draft.cards)}
                onChange={(cards) => set('cards', fromRepeatableCards(cards))}
                fieldLabel="효능 기전"
                fieldPlaceholder="예: 혈액순환·온열"
                perspectiveOptions={mechanismOptions}
                addLabel="+ 효능 카드 추가"
              />
              <div className="hint" style={{ marginTop: 8 }}>
                카드마다 효능 기전·설명·약점 태그를 단다. 고객 화면에선 약점 태그가 겹치는 효능 카드가 노출된다.
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
