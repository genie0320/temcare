import type { QuestionOption } from '../../core/survey/types'

// 문항 선택지(sc_009 UI요소 3번). 다중택일(라디오)과 다지선다(체크박스)를 한 컴포넌트로
// 처리한다 — 고르는 개수만 다르고 생김새·상호작용은 같기 때문이다.
//
// 실제 <input type="radio">를 쓰지 않고 버튼으로 그린 이유: 카드 전체가 탭 영역이어야
// 모바일에서 누르기 쉽고, 화면설계서의 지문 카드도 그 형태다. 접근성은 role/aria로 맞춘다.

interface ChoiceListProps {
  options: QuestionOption[]
  selected: string[]
  multiple: boolean
  onChange: (optionIds: string[]) => void
}

export function ChoiceList({ options, selected, multiple, onChange }: ChoiceListProps) {
  function toggle(optionId: string) {
    if (!multiple) {
      onChange([optionId])
      return
    }
    onChange(
      selected.includes(optionId) ? selected.filter((id) => id !== optionId) : [...selected, optionId],
    )
  }

  return (
    <div className="flex flex-col gap-sm" role={multiple ? 'group' : 'radiogroup'}>
      {options.map((option) => {
        const isOn = selected.includes(option.id)
        return (
          <button
            key={option.id}
            type="button"
            role={multiple ? 'checkbox' : 'radio'}
            aria-checked={isOn}
            onClick={() => toggle(option.id)}
            className={[
              'flex items-center gap-md rounded-md border px-md py-md text-left text-body transition-colors',
              isOn ? 'border-primary bg-primary-soft font-bold text-primary-dark' : 'border-border bg-surface',
            ].join(' ')}
          >
            <span
              aria-hidden
              className={[
                'flex h-[20px] w-[20px] shrink-0 items-center justify-center border text-caption',
                multiple ? 'rounded-sm' : 'rounded-pill',
                isOn ? 'border-primary bg-primary text-white' : 'border-gray-300 bg-surface',
              ].join(' ')}
            >
              {isOn ? '✓' : ''}
            </span>
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
