import type { QuestionOption } from '../../core/survey/types'

// 슬라이더형 문항(PPT SURVEY-02 · docs/06_decisions.md #25).
// "3~5개의 중단점을 가지고, 사용자가 선택한 중단점의 번호를 저장한다."
//
// ★ 이건 **구간(시작~끝) 선택이 아니라 점 하나 선택**이다. 그래서 지나온 트랙을
//   채우지 않는다 — 채우면 "여기서 저기까지"로 읽힌다. 트랙은 눈금자일 뿐이고,
//   강조되는 것은 고른 점 하나뿐이다.
// ★ 저장되는 값은 중단점 **번호(1부터인 정수)** 다. 화면만 슬라이더이고 데이터는
//   int라는 뜻이며, 변환은 SurveyRunScreen에서 한다.
//
// 중단점 개수는 문항마다 다르므로 options.length에서 그대로 읽는다 — 개수를 상수로
// 박아두면 문항이 바뀔 때 깨진다.

interface SliderChoiceProps {
  options: QuestionOption[]
  selected: string[]
  onChange: (optionIds: string[]) => void
}

export function SliderChoice({ options, selected, onChange }: SliderChoiceProps) {
  const selectedIndex = options.findIndex((o) => o.id === selected[0])

  return (
    <div className="flex flex-col gap-md">
      {/* 눈금자. 트랙은 늘 같은 회색이고 채워지지 않는다(구간 아님).
          눈금 사이 간격은 flex-1로 균등 분배한다(grid 안 씀 — §7-4). */}
      <div className="flex items-center px-xs">
        {options.map((option, index) => {
          const isOn = index === selectedIndex
          return (
            <div key={option.id} className="flex flex-1 items-center last:flex-none">
              <button
                type="button"
                role="radio"
                aria-checked={isOn}
                aria-label={option.label}
                onClick={() => onChange([option.id])}
                className="flex shrink-0 items-center justify-center p-xs"
              >
                <span
                  className={[
                    'block rounded-pill transition-all',
                    isOn
                      ? 'h-[24px] w-[24px] bg-primary ring-4 ring-primary-soft'
                      : 'h-[12px] w-[12px] bg-gray-300',
                  ].join(' ')}
                />
              </button>
              {index < options.length - 1 ? (
                <span className="h-[3px] flex-1 rounded-pill bg-gray-200" />
              ) : null}
            </div>
          )
        })}
      </div>

      {/* 라벨은 양끝과 고른 점만 글자로 보여준다 — 전부 쓰면 모바일 폭에서 겹친다.
          양끝을 고른 경우엔 가운데를 비우고 그 끝 라벨을 강조한다. 안 그러면 같은
          글자가 두 번 보여서 오작동처럼 읽힌다. */}
      {(() => {
        const lastIndex = options.length - 1
        const isEnd = selectedIndex === 0 || selectedIndex === lastIndex
        const strong = 'font-bold text-primary-dark'
        return (
          <div className="flex justify-between text-caption text-muted">
            <span className={selectedIndex === 0 ? strong : ''}>{options[0]?.label}</span>
            <span className={strong}>
              {selectedIndex < 0 ? '하나를 골라주세요' : isEnd ? '' : options[selectedIndex].label}
            </span>
            <span className={selectedIndex === lastIndex ? strong : ''}>{options[lastIndex]?.label}</span>
          </div>
        )
      })()}
    </div>
  )
}
