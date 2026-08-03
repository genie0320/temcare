import type { ReactNode } from 'react'

// 고객 화면의 바깥 틀. 모든 화면이 이걸 쓴다.
//
// 레이아웃은 flexbox만 쓴다 — CSS Grid·float·sticky를 피하는 것이 RN 전환 대비의
// 네 가지 중 하나다(docs/08_tech_stack.md §7-4).
//
// 데스크톱 브라우저에서도 개발하므로 가운데 정렬된 모바일 폭 컬럼으로 그린다.
// 실제 사용은 모바일 웹이라 폭 제한이 걸릴 일이 거의 없다.

interface ScreenProps {
  children: ReactNode
  /** 화면 하단에 고정으로 붙는 영역(주로 CTA 버튼). 스크롤과 무관하게 항상 보인다. */
  footer?: ReactNode
  /** 하단 탭바. footer와 달리 좌우 여백 없이 화면 폭을 꽉 채운다. */
  tabBar?: ReactNode
  /** 상단 바(TopBar 등). 스크롤되지 않는다. */
  header?: ReactNode
  /** 스플래시처럼 내용을 세로 가운데에 두고 싶을 때. */
  center?: boolean
  /** 히어로 배경이 화면 끝까지 닿아야 할 때 좌우 여백을 뺀다. */
  bleed?: boolean
  /** 상단 자리를 아예 비운다. 스플래시처럼 '앱 화면'이 아닌 곳에서만 쓴다. */
  bare?: boolean
}

/** TopBar의 높이. 상단 바가 없는 화면도 같은 만큼 비워 둔다(아래 주석). */
const TOP_BAR_HEIGHT = 'h-[52px]'

export function Screen({
  children,
  footer,
  tabBar,
  header,
  center = false,
  bleed = false,
  bare = false,
}: ScreenProps) {
  return (
    <div className="flex min-h-screen justify-center bg-gray-100">
      <div className="flex w-full max-w-[430px] flex-col bg-bg">
        {/* ★ 상단 바가 없는 화면도 **같은 높이를 비워 둔다.**
            안 그러면 상단 바가 있는 화면(가입·동의)과 없는 화면(닉네임·접근권한)을
            오갈 때 본문이 52px씩 위아래로 튄다. 한 화면씩 보면 멀쩡한데 눌러서
            넘어가 보면 "매끄럽지 않다"고 느껴지는 원인이 이것이다.
            디자인을 바꾸는 게 아니라 리듬만 맞추는 것이라 여기 한 곳에서 처리한다. */}
        {header ?? (bare ? null : <div className={`${TOP_BAR_HEIGHT} shrink-0`} />)}
        <main
          className={[
            'flex flex-1 flex-col overflow-y-auto',
            bleed ? '' : 'px-lg',
            center ? 'justify-center' : '',
          ].join(' ')}
        >
          {children}
        </main>
        {footer ? <div className="flex flex-col gap-sm px-lg pb-lg pt-md">{footer}</div> : null}
        {tabBar}
      </div>
    </div>
  )
}
