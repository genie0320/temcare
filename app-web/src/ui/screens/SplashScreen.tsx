import { useEffect } from 'react'
import { useNavigate } from 'react-router'

import { useAuthStore } from '../../core/store/auth'
import { Screen } from '../components/Screen'
import { ROUTES } from '../routes'

// sc_090 스플래시 — 앱 최초 실행 시 로딩 화면.
// 명세서: "로그인 상태에 따라 sc_091(미로그인) 또는 sc_101(로그인 유지 시)"이었으나
// 결정 #13으로 흐름이 뒤집혀, 미로그인은 sc_091(로그인)이 아니라 sc_004a(문진 유도)로 간다.

export function SplashScreen() {
  const navigate = useNavigate()
  const status = useAuthStore((s) => s.status)
  const bootstrap = useAuthStore((s) => s.bootstrap)

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  useEffect(() => {
    if (status === 'loading') return
    // replace: 뒤로가기로 스플래시에 다시 걸리지 않게 한다.
    navigate(status === 'authenticated' ? ROUTES.home : ROUTES.surveyIntro, { replace: true })
  }, [status, navigate])

  return (
    <Screen center>
      <div className="flex flex-col items-center gap-md">
        <div className="flex h-[96px] w-[96px] items-center justify-center rounded-xl bg-primary text-hero font-bold text-white">
          올라
        </div>
        <p className="text-hint text-muted">내 몸 사용설명서</p>
      </div>
    </Screen>
  )
}
