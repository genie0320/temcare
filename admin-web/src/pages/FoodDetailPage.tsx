import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, SegToggle, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import { useCrudDetail } from '../hooks/useCrudDetail'
import type { FoodDetail, FoodDraft, FoodPolarity } from '../types/food'

const EMPTY_DRAFT: FoodDraft = {
  polarity: '권장',
  foods: '',
  component: '',
  description: '',
  image: '',
  status: '게시',
  sort: 0,
  weakness_ids: [],
}

export function FoodDetailPage() {
  const crud = useCrudDetail<FoodDraft, FoodDetail>({
    resource: 'foods',
    queryKey: 'food',
    listQueryKey: 'foods',
    basePath: '/content/foods',
    empty: EMPTY_DRAFT,
    required: [
      { field: 'polarity', message: '극성(타입)은 필수다.' },
      { field: 'foods', message: '식품(항목명)은 필수다.' },
      { field: 'description', message: '설명은 필수다.' },
      { field: 'weakness_ids', message: '관련 약점은 필수다. 없으면 체질 결과화면에 자동 노출되지 않는다.' },
    ],
    deleteConfirm: '이 식품군을 삭제할까? 약점 태그 연결도 함께 사라진다.',
    alsoInvalidate: ['food-components'],
  })
  const { draft, set, data, isNew } = crud

  const { data: componentOptions } = useQuery({
    queryKey: ['food-components'],
    queryFn: () => apiGet<string[]>('/content/food-components/'),
  })

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '식품군 상세 · 새 식품군' : `식품군 상세 · ${data?.foods ?? ''}`}
      backTo="/content/foods"
    >
      <Card title="기본정보">
        <div className="form-grid">
          <FormRow label="극성(타입)" required>
            <SegToggle value={draft.polarity} options={['권장', '제한'] as FoodPolarity[]} onChange={(v) => set('polarity', v)} />
          </FormRow>
          <FormRow label="식품" required>
            <TextArea value={draft.foods} onChange={(v) => set('foods', v)} placeholder="예: 시금치·케일·브로콜리·오이·토마토" />
          </FormRow>
          <FormRow label="핵심성분">
            <TextInput
              value={draft.component}
              onChange={(v) => set('component', v)}
              placeholder="예: 칼륨 (선택)"
              listOptions={componentOptions}
            />
            <div className="hint">자유 입력이다. 앞서 쓴 값이 있으면 후보로 떠서 표기를 통일할 수 있다.</div>
          </FormRow>
          <FormRow label="설명" required>
            <TextArea value={draft.description} onChange={(v) => set('description', v)} placeholder="이 식품군이 어떤 도움을 주는지" />
          </FormRow>
          <FormRow label="대표 이미지">
            <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_025" />
          </FormRow>
          <FormRow label="관련 약점" required>
            <WeaknessTagPicker selectedIds={draft.weakness_ids} onChange={(ids) => set('weakness_ids', ids)} />
          </FormRow>
        </div>
      </Card>
    </CrudDetailPage>
  )
}
