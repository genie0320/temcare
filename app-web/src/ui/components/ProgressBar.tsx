// 문진 진행률(sc_009 UI요소 1번). 현재 문항 / 총 문항.

interface ProgressBarProps {
  current: number
  total: number
}

export function ProgressBar({ current, total }: ProgressBarProps) {
  const percent = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div className="flex flex-col gap-xs">
      <div
        className="h-[6px] w-full overflow-hidden rounded-pill bg-gray-200"
        role="progressbar"
        aria-valuenow={current}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label="문진 진행률"
      >
        <div className="h-full rounded-pill bg-primary transition-all" style={{ width: `${percent}%` }} />
      </div>
      <span className="text-caption text-faint">
        {current} / {total}
      </span>
    </div>
  )
}
