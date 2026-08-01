import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { apiDelete, apiGet, apiPatch, apiPost } from '../api/client'
import { Card, DetailLayout } from '../components/DetailLayout'
import { FormRow, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { MetaPanel } from '../components/MetaPanel'
import { PageHead } from '../components/PageHead'
import { PublishBox } from '../components/PublishBox'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import type { IllnessDetail, IllnessDraft } from '../types/illness'

const EMPTY_DRAFT: IllnessDraft = {
  name: '',
  description: '',
  image: '',
  status: '게시',
  sort: 0,
  weakness_ids: [],
}

export function IllnessDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['illness', id],
    queryFn: () => apiGet<IllnessDetail>(`/content/illnesses/${id}/`),
    enabled: !isNew,
  })

  const [draft, setDraft] = useState<IllnessDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof IllnessDraft>(key: K, value: IllnessDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.name.trim()) {
      setErrorMsg('항목명은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<IllnessDetail>('/content/illnesses/', draft)
        : await apiPatch<IllnessDetail>(`/content/illnesses/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['illnesses'] })
      await queryClient.invalidateQueries({ queryKey: ['illness'] })
      navigate(`/content/illnesses/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 예측질환을 삭제할까? 약점 태그 연결이 해제되고, 체질 발병율 지정에서도 연결이 풀린다.')) return
    await apiDelete(`/content/illnesses/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['illnesses'] })
    navigate('/content/illnesses')
  }

  return (
    <>
      <PageHead title={isNew ? '예측질환 상세 · 새 예측질환' : `예측질환 상세 · ${data?.name ?? ''}`} backTo="/content/illnesses" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="항목명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 소화기질환" />
                </FormRow>
                <FormRow label="항목설명">
                  <TextArea value={draft.description} onChange={(v) => set('description', v)} placeholder="질환 상세 설명(선택)" />
                </FormRow>
                <FormRow label="대표 이미지">
                  <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_007b" />
                </FormRow>
                <FormRow label="연결 약점" required>
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
