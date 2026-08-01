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
import type { HealthSignDetail, HealthSignDraft } from '../types/healthSign'

const EMPTY_DRAFT: HealthSignDraft = {
  name: '',
  note: '',
  image: '',
  status: '게시',
  sort: 0,
  weakness_ids: [],
}

export function HealthSignDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['health-sign', id],
    queryFn: () => apiGet<HealthSignDetail>(`/content/health-signs/${id}/`),
    enabled: !isNew,
  })

  const [draft, setDraft] = useState<HealthSignDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof HealthSignDraft>(key: K, value: HealthSignDraft[K]) {
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
        ? await apiPost<HealthSignDetail>('/content/health-signs/', draft)
        : await apiPatch<HealthSignDetail>(`/content/health-signs/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['health-signs'] })
      await queryClient.invalidateQueries({ queryKey: ['health-sign'] })
      navigate(`/content/health-signs/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 건강신호를 삭제할까? 약점 태그 연결도 함께 사라진다.')) return
    await apiDelete(`/content/health-signs/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['health-signs'] })
    navigate('/content/health-signs')
  }

  return (
    <>
      <PageHead title={isNew ? '건강신호 상세 · 새 건강신호' : `건강신호 상세 · ${data?.name ?? ''}`} backTo="/content/health-signs" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="항목명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 척추/관절이 아프다" />
                </FormRow>
                <FormRow label="항목설명">
                  <TextArea value={draft.note} onChange={(v) => set('note', v)} placeholder="짧은 관점/설명(선택)" />
                </FormRow>
                <FormRow label="대표 이미지">
                  <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_007a" />
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
