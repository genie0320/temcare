import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../api/client'
import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { RepeatableCards, type RepeatableCardItem } from '../components/RepeatableCards'
import { useCrudDetail } from '../hooks/useCrudDetail'
import type { HerbCardDraft, HerbDetail, HerbDraft } from '../types/herb'

const EMPTY_DRAFT: HerbDraft = {
  name: '',
  hanja: '',
  image: '',
  status: '게시',
  sort: 0,
  cards: [{ mechanism: '', description: '', weakness_ids: [] }],
}

// RepeatableCards는 {perspective, description, weakness_ids} 모양을 쓴다(영양소가 먼저
// 그 이름으로 만들어졌다). 약재는 필드명이 mechanism이라 여기서만 얇게 맞바꾼다 —
// 공용 컴포넌트에 화면마다 다른 필드명을 넣느니 호출부에서 변환하는 편이 더 단순하다.
function toRepeatableCards(cards: HerbCardDraft[]): RepeatableCardItem[] {
  return cards.map((c) => ({ perspective: c.mechanism, description: c.description, weakness_ids: c.weakness_ids }))
}

function fromRepeatableCards(cards: RepeatableCardItem[]): HerbCardDraft[] {
  return cards.map((c) => ({ mechanism: c.perspective, description: c.description, weakness_ids: c.weakness_ids }))
}

export function HerbDetailPage() {
  const crud = useCrudDetail<HerbDraft, HerbDetail>({
    resource: 'herbs',
    queryKey: 'herb',
    listQueryKey: 'herbs',
    basePath: '/content/herbs',
    empty: EMPTY_DRAFT,
    required: [{ field: 'name', message: '약재명은 필수다.' }],
    deleteConfirm: '이 약재를 삭제할까? 효능 카드·약점 태그도 함께 사라진다.',
    alsoInvalidate: ['herb-mechanisms'],
  })
  const { draft, set, data, isNew } = crud

  const { data: mechanismOptions } = useQuery({
    queryKey: ['herb-mechanisms'],
    queryFn: () => apiGet<string[]>('/content/herb-mechanisms/'),
  })

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '약재 상세 · 새 약재' : `약재 상세 · ${data?.name ?? ''}`}
      backTo="/content/herbs"
    >
      <Card title="기본정보">
        <div className="form-grid">
          <FormRow label="약재명" required>
            <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 육계" />
          </FormRow>
          <FormRow label="한자/생약명">
            <TextInput value={draft.hanja} onChange={(v) => set('hanja', v)} placeholder="예: 肉桂 (Cinnamomi Cortex)" />
          </FormRow>
          <FormRow label="대표 이미지">
            <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_023" />
          </FormRow>
        </div>
      </Card>

      <Card title="약점별 효능 카드" sub="같은 약재, 다른 효능">
        <RepeatableCards
          cards={toRepeatableCards(draft.cards)}
          onChange={(cards) => set('cards', fromRepeatableCards(cards))}
          fieldLabel="효능 기전"
          fieldPlaceholder="예: 혈액순환·온열"
          perspectiveOptions={mechanismOptions}
          addLabel="+ 효능 카드 추가"
        />
        <div className="hint" style={{ marginTop: 8 }}>
          카드마다 효능 기전·설명·약점 태그를 단다. 고객 화면에선 약점 태그가 겹치는 효능 카드가 노출된다.
        </div>
      </Card>
    </CrudDetailPage>
  )
}
