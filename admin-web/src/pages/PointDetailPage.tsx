import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import { useCrudDetail } from '../hooks/useCrudDetail'
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
  const crud = useCrudDetail<PointDraft, PointDetail>({
    resource: 'points',
    queryKey: 'point',
    listQueryKey: 'points',
    basePath: '/content/points',
    empty: EMPTY_DRAFT,
    required: [
      { field: 'name', message: '혈자리명은 필수다.' },
      { field: 'description', message: '설명은 필수다.' },
      { field: 'location', message: '위치는 필수다.' },
      { field: 'weakness_ids', message: '관련 약점은 필수다. 없으면 체질 결과화면에 자동 노출되지 않는다.' },
    ],
    deleteConfirm: '이 혈자리를 삭제할까? 약점 태그 연결도 함께 사라진다.',
  })
  const { draft, set, data, isNew } = crud

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '혈자리 상세 · 새 혈자리' : `혈자리 상세 · ${data?.name ?? ''}`}
      backTo="/content/points"
    >
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
    </CrudDetailPage>
  )
}
