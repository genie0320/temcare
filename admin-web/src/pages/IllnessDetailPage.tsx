import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import { useCrudDetail } from '../hooks/useCrudDetail'
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
  const crud = useCrudDetail<IllnessDraft, IllnessDetail>({
    resource: 'illnesses',
    queryKey: 'illness',
    listQueryKey: 'illnesses',
    basePath: '/content/illnesses',
    empty: EMPTY_DRAFT,
    required: [
      { field: 'name', message: '항목명은 필수다.' },
      { field: 'weakness_ids', message: '연결 약점은 필수다. 없으면 체질 결과화면에 자동 노출되지 않는다.' },
    ],
    deleteConfirm: '이 예측질환을 삭제할까? 약점 태그 연결이 해제되고, 체질 발병율 지정에서도 연결이 풀린다.',
  })
  const { draft, set, data, isNew } = crud

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '예측질환 상세 · 새 예측질환' : `예측질환 상세 · ${data?.name ?? ''}`}
      backTo="/content/illnesses"
    >
      <Card title="기본정보">
        <div className="form-grid">
          <FormRow label="항목명" required>
            <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 소화기질환" />
          </FormRow>
          <FormRow label="항목설명">
            <TextArea
              value={draft.description}
              onChange={(v) => set('description', v)}
              placeholder="질환 상세 설명(선택)"
            />
          </FormRow>
          <FormRow label="대표 이미지">
            <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_007b" />
          </FormRow>
          <FormRow label="연결 약점" required>
            <WeaknessTagPicker
              selectedIds={draft.weakness_ids}
              onChange={(ids) => set('weakness_ids', ids)}
            />
          </FormRow>
        </div>
      </Card>
    </CrudDetailPage>
  )
}
