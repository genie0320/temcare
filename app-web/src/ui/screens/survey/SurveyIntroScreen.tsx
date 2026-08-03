import { useNavigate } from 'react-router'

import { Button } from '../../components/Button'
import { Screen } from '../../components/Screen'
import { ROUTES } from '../../routes'

// sc_004a 문진 유도 — 미문진 사용자에게 문진을 유도.
//
// ★ 여기가 비로그인 진입점이다(결정 #13). 로그인부터 요구하지 않는다 —
//   카톡 공유로 들어온 사람이 첫 화면에서 로그인을 만나면 이탈하기 때문.
//
// ★ 다만 이 화면은 **공유링크 유입자와 오가닉 유입자가 같이 도착하는 곳**이다.
//   앱을 직접 켠 기존 회원(세션 만료·로그아웃 상태)도 여기로 온다. 그래서 로그인은
//   눈에 띄는 통로여야 한다 — 처음엔 작은 텍스트 링크였는데, 재방문자가 문진을
//   다시 풀어야 하는 것처럼 보여서 버튼으로 올렸다.
//   진입 경로별로 흐름을 나누지는 않는다(#13) — 나누는 건 '강조'까지다.

export function SurveyIntroScreen() {
  const navigate = useNavigate()

  return (
    <Screen
      footer={
        <>
          <Button onClick={() => navigate(ROUTES.surveyAbout)}>문진 시작하기</Button>
          <Button variant="ghost" onClick={() => navigate(ROUTES.signup, { state: { mode: 'login' } })}>
            이미 계정이 있어요 · 로그인
          </Button>
        </>
      }
    >
      <div className="flex flex-1 flex-col justify-center gap-lg py-xl">
        {/* 키비주얼(UI요소 1번). 일러스트는 아직 없어 자리만 잡아 둔다. */}
        <div className="flex h-[180px] items-center justify-center rounded-xl bg-primary-soft text-hero">
          🧬
        </div>
        <div className="flex flex-col gap-sm">
          <h1 className="text-hero font-extrabold leading-tight">
            당신의 체질을
            <br />
            알아보세요
          </h1>
          <p className="text-body text-muted">
            타고난 체질은 평생 바뀌지 않아요.
            <br />몇 가지 질문으로 64가지 TEM 체질 중 내 자리를 찾아드릴게요.
          </p>
        </div>
        <p className="text-caption text-faint">가입하지 않아도 지금 바로 시작할 수 있어요.</p>
      </div>
    </Screen>
  )
}
