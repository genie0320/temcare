import { useNavigate } from 'react-router'

import { ROUTES } from '../routes'

// 하단 탭. **1차는 홈/더보기 2탭**이다(명세서 v5 sc_101 비고).
//
// v4까지는 홈/TEM라이프/트래커/더보기 4탭이었는데, TEM라이프는 2차로 이연됐고(#11)
// 트래커는 보류라(#10) 1차에는 채울 탭이 둘뿐이다. 빈 탭을 미리 세워두면
// "곧 생긴다"는 신호가 되어 범위가 다시 부푼다.

type TabKey = 'home' | 'more'

// ★ '더보기'(sc_023)는 M5라 아직 화면이 없다. 예전에는 홈으로 보내 두었는데,
//   눌러도 아무 일이 없는 탭은 "고장났나?"로 읽힌다 — 눌러보며 확인하는 자리에서는
//   특히 그렇다. 갈 곳이 생길 때까지는 **눌리지 않는 상태로 그대로 보여준다.**
//   빈 화면을 만들어 붙이지 않는 이유는 그게 "곧 생긴다"는 신호가 되어 범위를
//   다시 부풀리기 때문이다(CLAUDE.md §2-3과 같은 이유).
const TABS: { key: TabKey; label: string; icon: string; route: string | null }[] = [
  { key: 'home', label: '홈', icon: '🏠', route: ROUTES.home },
  { key: 'more', label: '더보기', icon: '☰', route: null },
]

export function TabBar({ active }: { active: TabKey }) {
  const navigate = useNavigate()

  return (
    <nav className="flex border-t border-border bg-surface">
      {TABS.map((tab) => {
        const ready = tab.route !== null
        return (
          <button
            key={tab.key}
            type="button"
            disabled={!ready}
            aria-current={active === tab.key ? 'page' : undefined}
            onClick={() => tab.route && navigate(tab.route)}
            className={[
              'flex flex-1 flex-col items-center gap-xs py-sm text-caption',
              active === tab.key ? 'font-bold text-primary-dark' : 'text-faint',
              ready ? 'cursor-pointer' : 'cursor-not-allowed opacity-40',
            ].join(' ')}
          >
            <span className="text-subtitle">{tab.icon}</span>
            {tab.label}
          </button>
        )
      })}
    </nav>
  )
}
