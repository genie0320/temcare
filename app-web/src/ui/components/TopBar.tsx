import { useNavigate } from 'react-router'

// 화면 상단 바. 뒤로가기 화살표는 화면설계서 모든 내부 화면에 공통으로 있다.

interface TopBarProps {
  title?: string
  /** 뒤로가기를 숨긴다(스플래시·결과 티저처럼 되돌아갈 곳이 없는 화면). */
  hideBack?: boolean
  /** 기본 동작(history.back) 대신 다른 곳으로 보내야 할 때. */
  onBack?: () => void
  /** 오른쪽에 붙일 요소(건너뛰기 링크 등). */
  right?: React.ReactNode
}

export function TopBar({ title, hideBack = false, onBack, right }: TopBarProps) {
  const navigate = useNavigate()

  return (
    <div className="flex h-[52px] shrink-0 items-center gap-sm px-lg">
      {hideBack ? (
        <span className="w-[24px]" />
      ) : (
        <button
          type="button"
          aria-label="뒤로 가기"
          className="flex w-[24px] items-center text-title text-muted"
          onClick={() => (onBack ? onBack() : navigate(-1))}
        >
          ←
        </button>
      )}
      <span className="flex-1 text-subtitle font-bold">{title}</span>
      {right}
    </div>
  )
}
