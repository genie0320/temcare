import { Button } from './Button'

// 되돌리기 어려운 행동 앞에 한 번 묻는 바텀시트.
//
// window.confirm을 쓰지 않는다 — 브라우저 기본 대화상자는 문구를 우리가 못 고르고,
// 모바일에서 도메인 이름이 같이 떠서 앱 안이 아니라 웹처럼 보인다.
//
// z-50: Screen의 하단 CTA가 DOM상 뒤에 있어 z-index가 없으면 그 위에 겹쳐 그려진다.

interface ConfirmSheetProps {
  title: string
  body?: string
  confirmLabel: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmSheet({
  title,
  body,
  confirmLabel,
  cancelLabel = '계속할래요',
  onConfirm,
  onCancel,
}: ConfirmSheetProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40" role="dialog" aria-modal>
      <div className="flex w-full max-w-[430px] flex-col gap-md rounded-t-xl bg-surface p-lg">
        <h2 className="text-subtitle font-extrabold">{title}</h2>
        {body ? <p className="text-body leading-relaxed text-muted">{body}</p> : null}
        <div className="flex flex-col gap-sm pt-xs">
          <Button onClick={onCancel}>{cancelLabel}</Button>
          <Button variant="text" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
