// 체형특성 게이지(sc_004b UI요소 4번).
//
// ★ body_min/body_max는 **0~4 인덱스**다. 0~100 값이 아니다(docs/06_decisions.md #19).
//   5개 구간 중 min~max에 해당하는 칸을 하이라이트한다.

const LABELS = ['매우 마름', '마름', '보통', '통통', '매우 비만']

interface BodyGaugeProps {
  min: number
  max: number
}

export function BodyGauge({ min, max }: BodyGaugeProps) {
  return (
    <div className="flex flex-col gap-sm">
      <div className="flex gap-xs">
        {LABELS.map((label, index) => {
          const inRange = index >= min && index <= max
          return (
            <div key={label} className="flex flex-1 flex-col items-center gap-xs">
              <span
                className={['h-[8px] w-full rounded-pill', inRange ? 'bg-primary' : 'bg-gray-200'].join(' ')}
              />
              <span className={['text-caption', inRange ? 'font-bold text-primary-dark' : 'text-faint'].join(' ')}>
                {label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
