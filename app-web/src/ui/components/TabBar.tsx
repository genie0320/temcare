import { useNavigate } from 'react-router'

import { ROUTES } from '../routes'

// 하단 탭. **1차는 홈/더보기 2탭**이다(명세서 v5 sc_101 비고).
//
// v4까지는 홈/TEM라이프/트래커/더보기 4탭이었는데, TEM라이프는 2차로 이연됐고(#11)
// 트래커는 보류라(#10) 1차에는 채울 탭이 둘뿐이다. 빈 탭을 미리 세워두면
// "곧 생긴다"는 신호가 되어 범위가 다시 부푼다.

type TabKey = 'home' | 'more'

const TABS: { key: TabKey; label: string; icon: string; route: string }[] = [
  { key: 'home', label: '홈', icon: '🏠', route: ROUTES.home },
  // 더보기(sc_023)는 M5다. 탭은 세워두되 아직 갈 곳이 없다.
  { key: 'more', label: '더보기', icon: '☰', route: ROUTES.home },
]

export function TabBar({ active }: { active: TabKey }) {
  const navigate = useNavigate()

  return (
    <nav className="flex border-t border-border bg-surface">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          aria-current={active === tab.key ? 'page' : undefined}
          onClick={() => navigate(tab.route)}
          className={[
            'flex flex-1 flex-col items-center gap-xs py-sm text-caption',
            active === tab.key ? 'font-bold text-primary-dark' : 'text-faint',
          ].join(' ')}
        >
          <span className="text-subtitle">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
