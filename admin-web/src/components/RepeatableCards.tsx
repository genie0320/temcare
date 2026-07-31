import { FormRow, TextArea } from './FormControls'
import { WeaknessTagPicker } from './WeaknessTagPicker'

export interface RepeatableCardItem {
  perspective: string
  description: string
  weakness_ids: string[]
}

interface RepeatableCardsProps {
  cards: RepeatableCardItem[]
  onChange: (cards: RepeatableCardItem[]) => void
  fieldLabel: string
  fieldPlaceholder?: string
  perspectiveOptions?: string[]
  addLabel?: string
}

const EMPTY_CARD: RepeatableCardItem = { perspective: '', description: '', weakness_ids: [] }

// docs/05_screen_conventions.md §C 반복 카드 리스트 — 마스터 1건 + 하위 카드 N건, 카드마다 약점 n:m.
// 영양소(관점)·약재(효능기전) 등 "카드=(항목×관점)" 구조의 화면이 공유해 쓴다.
export function RepeatableCards({
  cards,
  onChange,
  fieldLabel,
  fieldPlaceholder,
  perspectiveOptions,
  addLabel = '+ 카드 추가',
}: RepeatableCardsProps) {
  const list = cards.length ? cards : [EMPTY_CARD]
  const datalistId = perspectiveOptions ? `rc-options-${fieldLabel}` : undefined

  function update(idx: number, patch: Partial<RepeatableCardItem>) {
    onChange(list.map((c, i) => (i === idx ? { ...c, ...patch } : c)))
  }

  function addCard() {
    onChange([...list, { ...EMPTY_CARD }])
  }

  function removeCard(idx: number) {
    const next = list.filter((_, i) => i !== idx)
    onChange(next.length ? next : [{ ...EMPTY_CARD }])
  }

  return (
    <>
      {list.map((card, idx) => (
        <div className="wcard" key={idx}>
          <div className="wcard-head">
            <b>카드 {idx + 1}</b>
            <button type="button" className="btn xs danger" style={{ marginLeft: 'auto' }} onClick={() => removeCard(idx)}>
              카드 삭제
            </button>
          </div>
          <div className="wcard-body">
            <div className="form-grid">
              <FormRow label={fieldLabel} required>
                <input
                  type="text"
                  value={card.perspective}
                  list={datalistId}
                  onChange={(e) => update(idx, { perspective: e.target.value })}
                  placeholder={fieldPlaceholder}
                  style={{ maxWidth: 280 }}
                />
              </FormRow>
              <FormRow label="설명" required>
                <TextArea
                  value={card.description}
                  onChange={(v) => update(idx, { description: v })}
                  placeholder="이 관점에서 어떤 도움을 주는지"
                />
              </FormRow>
              <FormRow label="약점 태그" required>
                <WeaknessTagPicker selectedIds={card.weakness_ids} onChange={(ids) => update(idx, { weakness_ids: ids })} />
              </FormRow>
            </div>
          </div>
        </div>
      ))}
      {perspectiveOptions && perspectiveOptions.length > 0 && (
        <datalist id={datalistId}>
          {perspectiveOptions.map((p) => (
            <option key={p} value={p} />
          ))}
        </datalist>
      )}
      <button type="button" className="addbtn" onClick={addCard}>
        {addLabel}
      </button>
    </>
  )
}
