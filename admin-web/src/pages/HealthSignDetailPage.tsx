import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import { useCrudDetail } from '../hooks/useCrudDetail'
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
  const crud = useCrudDetail<HealthSignDraft, HealthSignDetail>({
    resource: 'health-signs',
    queryKey: 'health-sign',
    listQueryKey: 'health-signs',
    basePath: '/content/health-signs',
    empty: EMPTY_DRAFT,
    required: [
      { field: 'name', message: '항목명은 필수다.' },
      { field: 'weakness_ids', message: '연결 약점은 필수다. 없으면 체질 결과화면에 자동 노출되지 않는다.' },
    ],
    deleteConfirm: '이 건강신호를 삭제할까? 약점 태그 연결도 함께 사라진다.',
  })
  const { draft, set, data, isNew } = crud

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '건강신호 상세 · 새 건강신호' : `건강신호 상세 · ${data?.name ?? ''}`}
      backTo="/content/health-signs"
    >
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
    </CrudDetailPage>
  )
}
