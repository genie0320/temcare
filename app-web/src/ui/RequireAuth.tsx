import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router'

import { useAuthStore } from '../core/store/auth'
import { Screen } from './components/Screen'
import { ROUTES } from './routes'

// 가입 이후 화면의 문지기. 세션이 없으면 문진 유도로 되돌린다.
//
// 로그인 화면이 아니라 문진 유도(sc_004a)로 보내는 이유: 결정 #13에서 첫 관문을
// 로그인이 아니라 문진으로 잡았기 때문이다. 새로 들어온 사람에게도 자연스럽다.

export function RequireAuth() {
  const status = useAuthStore((s) => s.status)
  const bootstrap = useAuthStore((s) => s.bootstrap)

  useEffect(() => {
    // 스플래시를 거치지 않고 URL로 바로 들어온 경우에도 세션을 확인해야 한다.
    if (status === 'loading') void bootstrap()
  }, [status, bootstrap])

  if (status === 'loading') {
    return (
      <Screen center>
        <p className="text-center text-body text-muted">불러오는 중…</p>
      </Screen>
    )
  }

  if (status === 'anonymous') return <Navigate to={ROUTES.surveyIntro} replace />

  return <Outlet />
}
