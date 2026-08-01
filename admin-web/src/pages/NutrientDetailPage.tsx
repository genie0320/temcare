import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { RepeatableCards } from '../components/RepeatableCards'
import { useCrudDetail } from '../hooks/useCrudDetail'
import type { NutrientDetail, NutrientDraft } from '../types/nutrient'

const EMPTY_DRAFT: NutrientDraft = {
  name: '',
  image: '',
  status: '게시',
  sort: 0,
  cards: [{ perspective: '', description: '', weakness_ids: [] }],
}

export function NutrientDetailPage() {
  const crud = useCrudDetail<NutrientDraft, NutrientDetail>({
    resource: 'nutrients',
    queryKey: 'nutrient',
    listQueryKey: 'nutrients',
    basePath: '/content/nutrients',
    empty: EMPTY_DRAFT,
    required: [{ field: 'name', message: '영양소명은 필수다.' }],
    deleteConfirm: '이 영양소를 삭제할까? 관점 카드·약점 태그도 함께 사라진다.',
    alsoInvalidate: ['nutrient-perspectives'],
  })
  const { draft, set, data, isNew } = crud

  const { data: perspectiveOptions } = useQuery({
    queryKey: ['nutrient-perspectives'],
    queryFn: () => apiGet<string[]>('/content/nutrient-perspectives/'),
  })

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '영양소 상세 · 새 영양소' : `영양소 상세 · ${data?.name ?? ''}`}
      backTo="/content/nutrients"
    >
      <Card title="기본정보">
        <div className="form-grid">
          <FormRow label="영양소명" required>
            <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 비타민 B-complex" />
          </FormRow>
          <FormRow label="대표 이미지">
            <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_022" />
          </FormRow>
        </div>
      </Card>

      <Card title="약점별 관점 카드" sub="같은 영양소, 다른 관점">
        <RepeatableCards
          cards={draft.cards}
          onChange={(cards) => set('cards', cards)}
          fieldLabel="개선분야(관점)"
          fieldPlaceholder="예: 대사회복"
          perspectiveOptions={perspectiveOptions}
          addLabel="+ 관점 카드 추가"
        />
        <div className="hint" style={{ marginTop: 8 }}>
          카드마다 관점(개선분야)·설명·약점 태그를 단다. 고객 화면에선 약점 태그가 겹치는 관점 카드가 노출된다.
        </div>
      </Card>
    </CrudDetailPage>
  )
}
