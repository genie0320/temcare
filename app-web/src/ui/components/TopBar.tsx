import { useNavigate } from 'react-router'

import { ROUTES } from '../routes'

// 화면 상단 바. 뒤로가기 화살표는 화면설계서 모든 내부 화면에 공통으로 있다.
//
// 상단 구성은 두 갈래로 통일한다(결정 #34).
//   · 온보딩·문진 흐름  → 제목 없이 뒤로가기만. 흐름을 따라가는 중이라 이름표가 필요없다.
//   · 로그인 이후 화면  → 제목 + 오른쪽 '홈'. 언제든 홈으로 나갈 수 있어야 한다.

interface TopBarProps {
  title?: string
  /** 뒤로가기를 숨긴다(스플래시·결과 티저처럼 되돌아갈 곳이 없는 화면). */
  hideBack?: boolean
  /** 기본 동작(history.back) 대신 다른 곳으로 보내야 할 때. */
  onBack?: () => void
  /**
   * 오른쪽에 '홈'을 붙인다. 로그인 이후 화면(결과·처방·한의원)의 공통 규칙이다.
   * 예전에는 결과 화면에만 손으로 붙어 있어서 처방·한의원에서는 나갈 문이
   * 브라우저 뒤로가기뿐이었다 — 화면마다 다른 것이 "매끄럽지 않다"의 정체였다.
   */
  homeLink?: boolean
  /** 그 밖에 오른쪽에 붙일 요소(건너뛰기 링크 등). homeLink와 같이 쓰지 않는다. */
  right?: React.ReactNode
}

export function TopBar({ title, hideBack = false, onBack, homeLink = false, right }: TopBarProps) {
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
      {homeLink ? (
        <button type="button" className="text-hint text-muted" onClick={() => navigate(ROUTES.home)}>
          홈
        </button>
      ) : (
        right
      )}
    </div>
  )
}
