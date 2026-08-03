import { useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { fetchMyResult } from '../../../core/api/result'
import { useAuthStore } from '../../../core/store/auth'
import { DataScreen } from '../../components/DataScreen'
import { TabBar } from '../../components/TabBar'
import { TopBar } from '../../components/TopBar'
import { ROUTES } from '../../routes'

// sc_101 메인 홈 — **1차는 축소 구성**이다(명세서 v5 비고).
//
// 넣는 것: 인사말 · 체질 요약 카드 · 문진 유도 배너(미문진일 때) · 처방 진입
// 빼는 것: 알림함(sc_109)·홈 팝업(sc_110)은 2차, 무드 트리거(sc_105)는 보류.
//          TEM라이프 추천 캐러셀도 2차 이연(결정 #11).
// 하단 탭도 1차에는 트래커·TEM라이프가 없어 **홈/더보기 2탭**으로 시작한다.

export function HomeScreen() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const query = useQuery({ queryKey: ['my-result'], queryFn: fetchMyResult })

  return (
    // gate를 걸지 않는다 — 홈은 결과가 없어도 정상적으로 보여야 하는 화면이다.
    // 다만 '불러오기 실패'와 '아직 문진 전'은 구분해야 한다. 예전에는 둘이 같아서
    // 이미 결과가 있는 사람에게도 "어떤 체질이신지 궁금해요"가 떴다.
    <DataScreen
      query={query}
      errorLabel="홈 정보를 불러오지 못했어요."
      header={<TopBar title="홈" hideBack />}
      tabBar={<TabBar active="home" />}
    >
      {(data) => {
      const hasResult = data.hasResult && data.found
      return (
      <div className="flex flex-col gap-lg py-lg">
        <div className="flex flex-col gap-xs">
          <h1 className="text-title font-extrabold leading-snug">
            {user?.nickname}님,
            <br />
            {hasResult ? '오늘도 내 몸을 아껴요.' : '어떤 체질이신지 궁금해요.'}
          </h1>
        </div>

        {hasResult ? (
          <button
            type="button"
            onClick={() => navigate(ROUTES.result)}
            className="flex flex-col gap-sm rounded-xl bg-surface p-md text-left"
          >
            <span className="text-caption text-faint">내 체질</span>
            <span className="text-subtitle font-extrabold">{data.name}</span>
            {data.nickname ? <span className="text-hint text-primary-dark">{data.nickname}</span> : null}
            <div className="flex flex-wrap gap-xs pt-xs">
              {(data.weaknesses ?? []).map((w) => (
                <span key={w.id} className="rounded-pill bg-primary-soft px-sm py-xs text-caption text-primary-dark">
                  {w.name}
                </span>
              ))}
            </div>
          </button>
        ) : (
          // 문진 유도 배너(sc_101 UI요소 6번) — 미문진일 때만.
          <button
            type="button"
            onClick={() => navigate(ROUTES.surveyIntro)}
            className="flex items-center gap-md rounded-xl bg-primary p-md text-left text-white"
          >
            <span className="text-title">🧬</span>
            <span className="flex-1 text-body font-bold">
              나의 TEM 체질,
              <br />5분만에 알아보기
            </span>
            <span className="text-title">›</span>
          </button>
        )}

        {/* 처방 진입(sc_007). 문진 전에는 보여줄 처방이 없으므로 결과가 있을 때만 낸다. */}
        {hasResult ? (
          <button
            type="button"
            onClick={() => navigate(ROUTES.prescription)}
            className="flex items-center gap-md rounded-xl bg-surface p-md text-left"
          >
            <span className="text-title">🌿</span>
            <span className="flex-1 text-body font-bold">내 몸을 아끼는 길</span>
            <span className="text-title text-gray-300">›</span>
          </button>
        ) : null}

        {/* 로그아웃은 원래 더보기(sc_023, M5)에 있어야 한다. 그런데 그때까지 로그아웃
            수단이 아예 없으면 **한번 가입한 뒤로는 가입 전 화면을 다시 볼 방법이 없다**.
            검수하는 쪽에서 이건 막다른 길이라 임시로 여기 둔다. sc_023이 생기면 옮긴다. */}
        <button
          type="button"
          onClick={async () => {
            await logout()
            navigate(ROUTES.surveyIntro, { replace: true })
          }}
          className="self-center py-md text-hint text-faint underline"
        >
          로그아웃
        </button>
      </div>
      )
      }}
    </DataScreen>
  )
}
