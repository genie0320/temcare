import { Link, Outlet, useLocation } from 'react-router'
import { useAuthStore } from '../store/auth'

const NAV = [
  { group: '체질/진단 관리', items: [{ to: '/content/weaknesses', icon: '🏷️', label: '약점태그 마스터' }] },
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
