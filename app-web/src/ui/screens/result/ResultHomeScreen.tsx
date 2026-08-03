import { useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { fetchMyResult } from '../../../core/api/result'
import { useAuthStore } from '../../../core/store/auth'
import { BodyGauge } from '../../components/BodyGauge'
import { Button } from '../../components/Button'
import { Screen } from '../../components/Screen'
import { TopBar } from '../../components/TopBar'
import { ROUTES } from '../../routes'
import { HealthSignSection, IllnessSection } from './ResultSections'

// sc_004b 체질분석결과 — **한 화면 스크롤**이다.
//
// 화면설계서 '체질분석결과(1/2)·(2/2)'가 정본이며, 두 장은 별개 화면이 아니라
// 한 화면의 위·아래다. 요소 번호를 그대로 따른다.
//
//   #1 닉네임+고정문구  #2 타입명 칩  #3 스노우플레이크  #4 체질 별명
//   #5 약점(WEAKNESS)  #6 이 체질은요…(체형)  #7 내 몸의 건강신호(아코디언)
//   #8 주의해야 할 질환(그래프)  #9 예상질환 카드(+#9a 모달)
//   #10 인생처방 보기  #11 체질검사 다시 진행해보기
//
// ★ 한때 sc_005(건강신호)·sc_006(예측질환)으로 화면을 쪼갰었다. 명세서 v5가
//   '요약 카드 → 이동'으로 적어 두어 그걸 따랐던 것인데, 설계서는 처음부터
//   한 화면이었다. 설계서를 따르고 두 경로는 이 화면으로 넘긴다(routes.ts).
//
// 📌 스노우플레이크 그래프는 데이터 소스가 미확정이라 자리만 잡아 두었다.

export function ResultHomeScreen() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const { data, isPending } = useQuery({ queryKey: ['my-result'], queryFn: fetchMyResult })

  if (isPending) {
    return (
      <Screen center>
        <p className="text-center text-body text-muted">불러오는 중…</p>
      </Screen>
    )
  }

  if (!data?.hasResult) {
    return (
      <Screen
        header={<TopBar hideBack />}
        center
        footer={<Button onClick={() => navigate(ROUTES.surveyIntro)}>문진 시작하기</Button>}
      >
        <p className="text-center text-body text-muted">아직 문진 결과가 없어요.</p>
      </Screen>
    )
  }

  if (!data.found) {
    // 개발 중에만 보이는 상태 — tem_type 시드가 6개뿐이다(📌).
    return (
      <Screen header={<TopBar hideBack />} center>
        <div className="flex flex-col items-center gap-sm text-center">
          <h1 className="text-title font-extrabold">{data.typeId}</h1>
          <p className="text-hint text-orange-500">
            이 체질의 콘텐츠가 아직 없어요. (개발용 시드 미완성)
          </p>
        </div>
      </Screen>
    )
  }

  return (
    <Screen
      header={
        <TopBar
          hideBack
          right={
            <button type="button" className="text-hint text-muted" onClick={() => navigate(ROUTES.home)}>
              홈
            </button>
          }
        />
      }
      footer={
        <>
          {/* #10 — 결과(판정)에서 처방(행동)으로 넘어가는 유일한 문(결정 #28). */}
          <Button onClick={() => navigate(ROUTES.prescription)}>내 체질 꼭맞춤 인생처방 보기</Button>
          {/* #11 */}
          <Button variant="text" onClick={() => navigate(ROUTES.surveyIntro)}>
            체질검사 다시 진행해보기
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-lg pb-lg">
        {/* #1 */}
        <h1 className="text-title font-extrabold leading-snug">
          {user?.nickname}님의
          <br />
          TEM체질분석결과 안내
        </h1>

        {/* #3 스노우플레이크 자리(📌 데이터 소스 미확정) */}
        <div className="flex h-[160px] items-center justify-center rounded-xl bg-primary-soft text-hero">
          ❄️
        </div>

        <div className="flex flex-col items-center gap-xs">
          {/* #2 */}
          <span className="rounded-pill bg-primary-soft px-md py-xs text-hint font-bold text-primary-dark">
            {data.typeId} · {data.name}
          </span>
          {/* #4 */}
          {data.nickname ? (
            <p className="text-center text-title font-extrabold leading-snug text-primary-dark">
              {data.nickname}
            </p>
          ) : null}
        </div>

        {/* #5 */}
        {data.weaknesses && data.weaknesses.length > 0 ? (
          <section className="flex flex-col gap-sm">
            <h2 className="text-caption font-bold tracking-widest text-faint">WEAKNESS</h2>
            <div className="flex flex-wrap gap-xs">
              {data.weaknesses.map((w) => (
                <span
                  key={w.id}
                  className="rounded-pill bg-surface px-md py-xs text-hint font-bold text-text"
                >
                  {w.name}
                </span>
              ))}
            </div>
          </section>
        ) : null}

        {/* #6 */}
        {data.body ? (
          <section className="flex flex-col gap-sm rounded-md bg-surface p-md">
            <h2 className="text-subtitle font-bold">이 체질은요…</h2>
            <BodyGauge min={data.body.min} max={data.body.max} />
            {data.body.desc ? <p className="text-hint text-muted">{data.body.desc}</p> : null}
          </section>
        ) : null}

        {/* #7 */}
        <section className="flex flex-col gap-sm">
          <h2 className="text-subtitle font-extrabold">내 몸의 건강신호</h2>
          <HealthSignSection signs={data.healthSigns ?? []} />
        </section>

        {/* #8 · #9 · #9a */}
        <section className="flex flex-col gap-sm">
          <h2 className="text-subtitle font-extrabold">주의해야 할 질환</h2>
          <IllnessSection illnesses={data.illnesses ?? []} />
        </section>

        <p className="text-caption text-faint">본 정보는 참고용이며 진단이 아닙니다.</p>
      </div>
    </Screen>
  )
}
