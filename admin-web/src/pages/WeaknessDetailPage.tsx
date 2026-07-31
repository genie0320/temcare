import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { apiDelete, apiGet, apiPatch, apiPost } from '../api/client'
import { Card, DetailLayout } from '../components/DetailLayout'
import { FormRow, TextArea, TextInput, SegToggle } from '../components/FormControls'
import { MetaPanel } from '../components/MetaPanel'
import { PageHead } from '../components/PageHead'
import { PublishBox } from '../components/PublishBox'
import type { WeaknessDetail, WeaknessDraft } from '../types/weakness'

const EMPTY_DRAFT: WeaknessDraft = {
  name: '',
  wtype: '약점',
  catchphrase: '',
  speaker: '',
  source: '',
  aphorism: '',
  status: '게시',
  sort: 0,
}

export function WeaknessDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['weakness', id],
    queryFn: () => apiGet<WeaknessDetail>(`/content/weaknesses/${id}/`),
    enabled: !isNew,
  })

  const [draft, setDraft] = useState<WeaknessDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof WeaknessDraft>(key: K, value: WeaknessDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.name.trim()) {
      setErrorMsg('약점명은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<WeaknessDetail>('/content/weaknesses/', draft)
        : await apiPatch<WeaknessDetail>(`/content/weaknesses/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['weaknesses'] })
      await queryClient.invalidateQueries({ queryKey: ['weakness'] })
      navigate(`/content/weaknesses/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 약점을 삭제할까? 콘텐츠에 연결된 태그도 함께 사라진다.')) return
    await apiDelete(`/content/weaknesses/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['weaknesses'] })
    navigate('/content/weaknesses')
  }

  return (
    <>
      <PageHead title={isNew ? '약점 상세 · 새 약점' : `약점 상세 · ${data?.name ?? ''}`} backTo="/content/weaknesses" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="타입" required>
                  <SegToggle value={draft.wtype} options={['약점', 'IDEA']} onChange={(v) => set('wtype', v)} />
                </FormRow>
                <FormRow label="약점명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} />
                </FormRow>
              </div>
            </Card>
            <Card title="캐치프레이즈" sub="처방화면 그룹 제목용(예: '똥 막힌 하수도')">
              <div className="form-grid">
                <FormRow label="캐치프레이즈">
                  <TextInput value={draft.catchphrase} onChange={(v) => set('catchphrase', v)} placeholder="예: 똥 막힌 하수도" />
                </FormRow>
              </div>
            </Card>
            <Card title="격언" sub="각 약점에 노출할 격언">
              <div className="form-grid">
                <FormRow label="화자">
                  <TextInput value={draft.speaker} onChange={(v) => set('speaker', v)} />
                </FormRow>
                <FormRow label="출처">
                  <TextInput value={draft.source} onChange={(v) => set('source', v)} />
                </FormRow>
                <FormRow label="격언">
                  <TextArea value={draft.aphorism} onChange={(v) => set('aphorism', v)} />
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
