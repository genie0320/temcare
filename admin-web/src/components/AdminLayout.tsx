import { Link, Outlet, useLocation } from 'react-router'
import { useAuthStore } from '../store/auth'

const NAV = [
  {
    group: '체질/진단 관리',
    items: [
      { to: '/content/tem-types', icon: '🧬', label: '64유형 마스터' },
      { to: '/content/weaknesses', icon: '🏷️', label: '약점태그 마스터' },
    ],
  },
  {
    group: '콘텐츠 관리',
    items: [
      { to: '/content/nutrients', icon: '💊', label: '영양소 마스터' },
      { to: '/content/herbs', icon: '🌿', label: '약재 마스터' },
      { to: '/content/foods', icon: '🥗', label: '식품군 마스터' },
      { to: '/content/points', icon: '📍', label: '혈자리 마스터' },
      { to: '/content/health-signs', icon: '🩺', label: '건강신호 마스터' },
      { to: '/content/illnesses', icon: '🔮', label: '예측질환 마스터' },
      { to: '/content/products', icon: '🛍️', label: '제품 마스터' },
      { to: '/content/articles', icon: '📄', label: '요법관리 마스터' },
    ],
  },
  {
    group: '템라이프',
    items: [{ to: '/content/life-articles', icon: '📰', label: '템라이프 마스터' }],
  },
  {
    group: '시스템',
    items: [
      { to: '/system/audit-logs', icon: '🧾', label: '감사로그 · 접속기록' },
      { to: '/system/design', icon: '🎨', label: '디자인 시스템' },
    ],
  },
]

export function AdminLayout() {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">올</div>
          <div>
            <b>올라케어</b>
            <span>관리자</span>
          </div>
        </div>
        <nav className="nav">
          {NAV.map((group) => (
            <div key={group.group}>
              <div className="nav-group">{group.group}</div>
              {group.items.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`nav-item${location.pathname.startsWith(item.to) ? ' active' : ''}`}
                >
                  <span className="ico">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
      </aside>
      <div className="main">
        <div className="topbar">
          <div className="spacer" />
          <div className="who">
            <div className="avatar">{user?.email?.[0]?.toUpperCase() ?? '?'}</div>
            {user?.email}
            <button className="btn ghost sm" onClick={() => logout()}>
              로그아웃
            </button>
          </div>
        </div>
        <div className="content">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
