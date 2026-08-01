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
import type { PointDetail, PointDraft } from '../types/point'

const EMPTY_DRAFT: PointDraft = {
  name: '',
  hanja: '',
  description: '',
  location: '',
  image: '',
  video: '',
  status: '게시',
  sort: 0,
  weakness_ids: [],
}

export function PointDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['point', id],
    queryFn: () => apiGet<PointDetail>(`/content/points/${id}/`),
    enabled: !isNew,
  })

  const [draft, setDraft] = useState<PointDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof PointDraft>(key: K, value: PointDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.name.trim()) {
      setErrorMsg('혈자리명은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<PointDetail>('/content/points/', draft)
        : await apiPatch<PointDetail>(`/content/points/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['points'] })
      await queryClient.invalidateQueries({ queryKey: ['point'] })
      navigate(`/content/points/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 혈자리를 삭제할까? 약점 태그 연결도 함께 사라진다.')) return
    await apiDelete(`/content/points/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['points'] })
    navigate('/content/points')
  }

  return (
    <>
      <PageHead title={isNew ? '혈자리 상세 · 새 혈자리' : `혈자리 상세 · ${data?.name ?? ''}`} backTo="/content/points" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="혈자리명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 합곡" />
                </FormRow>
                <FormRow label="한자">
                  <TextInput value={draft.hanja} onChange={(v) => set('hanja', v)} placeholder="예: 合谷" />
                </FormRow>
                <FormRow label="설명" required>
                  <TextArea value={draft.description} onChange={(v) => set('description', v)} placeholder="이 혈자리가 어떤 도움을 주는지" />
                </FormRow>
                <FormRow label="위치" required>
                  <TextArea value={draft.location} onChange={(v) => set('location', v)} placeholder="짚는 위치를 설명" />
                </FormRow>
                <FormRow label="대표 이미지">
                  <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_026" />
                </FormRow>
                <FormRow label="관련 영상 URL">
                  <TextInput value={draft.video} onChange={(v) => set('video', v)} placeholder="https://..." />
                  <div className="hint">유튜브 등 시연 영상 링크(선택).</div>
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
