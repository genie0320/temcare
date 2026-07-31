import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { apiDelete, apiGet, apiPatch, apiPost } from '../api/client'
import { BodySlider } from '../components/BodySlider'
import { Card, DetailLayout } from '../components/DetailLayout'
import { CuratedPickList } from '../components/CuratedPickList'
import { FormRow, TextArea, TextInput } from '../components/FormControls'
import { IllnessRateRows } from '../components/IllnessRateRows'
import { MetaPanel } from '../components/MetaPanel'
import { PageHead } from '../components/PageHead'
import { PublishBox } from '../components/PublishBox'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import type { TemTypeDetail, TemTypeDraft } from '../types/temType'

const EMPTY_DRAFT: TemTypeDraft = {
  name: '',
  nickname: '',
  body_min: 2,
  body_max: 2,
  body_desc: '',
  herb_title: '',
  herb_desc: '',
  status: '게시',
  sort: 0,
  weakness_ids: [],
  illnesses: [],
  nutrient_card_ids: [],
  herb_card_ids: [],
  food_ids: [],
}

export function TemTypeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['tem-type', id],
    queryFn: () => apiGet<TemTypeDetail>(`/content/tem-types/${id}/`),
    enabled: !isNew,
  })

  const [draft, setDraft] = useState<TemTypeDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof TemTypeDraft>(key: K, value: TemTypeDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.name.trim()) {
      setErrorMsg('체질명은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<TemTypeDetail>('/content/tem-types/', draft)
        : await apiPatch<TemTypeDetail>(`/content/tem-types/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['tem-types'] })
      await queryClient.invalidateQueries({ queryKey: ['tem-type'] })
      navigate(`/content/tem-types/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 체질을 삭제할까? 약점·예측질환·큐레이션 연결도 함께 사라진다.')) return
    await apiDelete(`/content/tem-types/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['tem-types'] })
    navigate('/content/tem-types')
  }

  return (
    <>
      <PageHead title={isNew ? '체질 상세 · 새 체질' : `체질 상세 · ${data?.name ?? ''}`} backTo="/content/tem-types" />
      <DetailLayout
        main={
          <>
            <div className="note">
              <span className="i">ℹ</span>
              <div>
                <b>영양요법·식이요법·인생처방</b>은 아래에서 직접 골라 담는다(큐레이션). <b>건강신호·지압·생활 관리법</b>은 약점
                태그가 겹치는 콘텐츠가 <b>자동 노출</b>되므로 여기서 관리하지 않는다.
              </div>
            </div>

            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="체질명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: TE-5" />
                </FormRow>
                <FormRow label="체질 별명">
                  <TextArea
                    value={draft.nickname}
                    onChange={(v) => set('nickname', v)}
                    placeholder="자유 텍스트. 고객 결과화면 상단에 노출된다."
                  />
                </FormRow>
                <FormRow label="관련 약점" required>
                  <WeaknessTagPicker selectedIds={draft.weakness_ids} onChange={(ids) => set('weakness_ids', ids)} />
                  <div className="hint">태그가 콘텐츠 자동 노출(건강신호·관리법)과 아래 큐레이션 후보의 기준이 된다.</div>
                </FormRow>
                <FormRow label="체형 특성" required>
                  <BodySlider lo={draft.body_min} hi={draft.body_max} onChange={(lo, hi) => setDraft((p) => ({ ...p, body_min: lo, body_max: hi }))} />
                  <TextArea value={draft.body_desc} onChange={(v) => set('body_desc', v)} placeholder="체형 특성 설명" />
                </FormRow>
              </div>
            </Card>

            <Card title="예측질환 발병율" sub="이 체질에 발병 가능성이 있는 질환과 비율(%)">
              <IllnessRateRows rows={draft.illnesses} onChange={(rows) => set('illnesses', rows)} />
            </Card>

            <Card title="영양요법" sub="관련 약점을 가진 영양소를 관점별로 큐레이션한다">
              <CuratedPickList
                label="영양소"
                ids={draft.nutrient_card_ids}
                weaknessIds={draft.weakness_ids}
                candidatesPath="/content/tem-type-candidates/nutrient-cards/"
                onChange={(ids) => set('nutrient_card_ids', ids)}
              />
            </Card>

            <Card title="인생처방 · 약재" sub="관련 약점을 가진 약재를 효능기전별로 큐레이션한다">
              <div className="form-grid">
                <FormRow label="제목">
                  <TextInput value={draft.herb_title} onChange={(v) => set('herb_title', v)} placeholder="예: 몸의 축을 데우는 인생처방" />
                </FormRow>
                <FormRow label="설명">
                  <TextArea
                    value={draft.herb_desc}
                    onChange={(v) => set('herb_desc', v)}
                    placeholder="약재 처방을 아우르는 설명 — 고객 화면 약재 섹션 상단에 노출"
                  />
                </FormRow>
              </div>
              <div style={{ marginTop: 12 }}>
                <CuratedPickList
                  label="약재"
                  ids={draft.herb_card_ids}
                  weaknessIds={draft.weakness_ids}
                  candidatesPath="/content/tem-type-candidates/herb-cards/"
                  onChange={(ids) => set('herb_card_ids', ids)}
                />
              </div>
            </Card>

            <Card title="식이요법 · 식품군" sub="관련 약점을 가진 식품군을 큐레이션한다(권장/제한 극성은 식품군 값 사용)">
              <CuratedPickList
                label="식품군"
                ids={draft.food_ids}
                weaknessIds={draft.weakness_ids}
                candidatesPath="/content/tem-type-candidates/foods/"
                onChange={(ids) => set('food_ids', ids)}
              />
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
