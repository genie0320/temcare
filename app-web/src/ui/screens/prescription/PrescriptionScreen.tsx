import { Fragment, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { fetchPrescription } from '../../../core/api/prescription'
import { DataScreen } from '../../components/DataScreen'
import { resultGate } from '../../components/ResultGate'
import { TopBar } from '../../components/TopBar'
import { ROUTES } from '../../routes'
import { DietStation, HerbSpotlight, LifeStation, NutritionStation } from './Stations'

// sc_007 처방 스트림 "내 몸을 아끼는 길" — 이 서비스의 가치가 전부 여기 있다.
//
// 영양 → 식이 → 생활 → 약재 4정거장(docs/06_decisions.md #2). 아래로 갈수록 색이
// 진해지고 약재가 끝판왕이다. **한 화면 스크롤**이며 정거장별로 나누지 않는다 —
// 탭할 일이 없어야 끝까지 내려간다.
//
// ★ 여기에 판정 정보(약점 설명·건강신호·질환)를 얹지 말 것. 체질에 **속한 것**은
//   결과화면(sc_004b), 체질을 **다스리는 것**만 여기다.
//
// 디자인 기준은 prototype/prescription_stream_mockup.html.

const STATIONS = [
  { key: 'nutrition', icon: '🥗', label: '영양' },
  { key: 'diet', icon: '🍽️', label: '식이' },
  { key: 'life', icon: '🌙', label: '생활' },
  { key: 'herb', icon: '🌿', label: '약재' },
] as const

export function PrescriptionScreen() {
  const navigate = useNavigate()
  const query = useQuery({ queryKey: ['prescription'], queryFn: fetchPrescription })

  return (
    <DataScreen
      query={query}
      gate={resultGate}
      errorLabel="인생처방을 불러오지 못했어요."
      header={<TopBar title="내 몸을 아끼는 길" homeLink />}
      bleed
    >
      {(data) => {
  const nutrition = data.nutrition ?? []
  const diet = data.diet ?? { good: [], limit: [] }
  const life = data.life ?? []
  const herb = data.herb ?? { title: '', desc: '', groups: [] }
  const hasHerb = herb.groups.length > 0

  return (
      <>
      {/* 히어로 — 여기서만 배경이 화면 끝까지 닿는다(Screen bleed). */}
      <div className="flex flex-col gap-sm bg-linear-to-b from-surface to-bg px-lg pb-lg">
        <span className="self-start rounded-pill bg-green-50 px-md py-xs text-caption font-bold text-primary-dark">
          🧬 {data.typeId}
          {(data.weaknesses ?? []).map((w) => ` · ${w.name}`).join('')}
        </span>
        <h1 className="text-hero font-extrabold leading-tight">
          내 몸을
          <br />
          아끼는 길
        </h1>
        <p className="text-hint text-muted">
          먹고 · 살고 · 다스리는 모든 것이
          <br />
          나를 아끼는 하나의 길이에요.
        </p>
        <JourneyStepper />
      </div>

      <div className="flex flex-col pb-lg pl-[48px] pr-md pt-md">
        {/* 스트림 척추. 정거장 ①~③을 관통하고 크레센도 직전에 끝난다 — 척추가
            스포트라이트까지 이어지면 약재가 '네 번째 항목'으로 보인다. */}
        <div className="relative flex flex-col">
          <span
            aria-hidden
            className="absolute -left-[19px] bottom-0 top-sm w-[3px] rounded-pill bg-linear-to-b from-green-100 via-green-500 to-green-700"
          />
          <Stage icon="🥗" title="영양" sub="매일 챙기면 좋은" lead="약점을 안에서부터 채우는 영양소예요.">
            {nutrition.length > 0 ? <NutritionStation items={nutrition} /> : <Empty />}
          </Stage>
          <Stage icon="🍽️" title="식이" sub="식탁 신호등" lead="오늘 뭘 더 먹고, 뭘 줄일지.">
            {diet.good.length + diet.limit.length > 0 ? (
              <DietStation good={diet.good} limit={diet.limit} />
            ) : (
              <Empty />
            )}
          </Stage>
          <Stage icon="🌙" title="생활" sub="하루 루틴" lead="몸에 스며드는 작은 습관.">
            {life.length > 0 ? <LifeStation items={life} /> : <Empty />}
          </Stage>
        </div>

        {hasHerb ? (
          <>
            <p className="my-sm text-center text-hint font-extrabold text-primary-dark">
              그리고 — 가장 강력한 한 가지
            </p>
            <div className="relative">
              <span
                aria-hidden
                className="absolute -left-[37px] top-0 flex h-[40px] w-[40px] items-center justify-center rounded-pill bg-linear-to-br from-green-500 to-green-700 text-subtitle shadow-lg"
              >
                🌿
              </span>
              <HerbSpotlight title={herb.title} desc={herb.desc} groups={herb.groups} />
            </div>
          </>
        ) : null}

        {/* ★ 깔때기의 출구(결정 #8). 스트림이 약재에서 끝나고 아무 데도 이어지지
            않으면 이 서비스의 목적이 사라진다. 약재 스포트라이트 바로 다음,
            가장 마음이 움직인 지점에 둔다. */}
        <button
          type="button"
          onClick={() => navigate(ROUTES.clinics)}
          className="mt-md flex flex-col gap-xs rounded-xl border border-border bg-surface p-md text-left"
        >
          <span className="text-caption font-bold text-primary-dark">다음 걸음</span>
          <span className="flex items-center gap-sm">
            <span className="flex-1 text-body font-extrabold leading-snug">
              이 처방을 정확히 받으려면?
              <br />
              협력 한의원 정밀 문진
            </span>
            <span className="text-title text-gray-300">›</span>
          </span>
          <span className="text-caption text-muted">
            앱 문진은 약식이에요. 130문항 정밀 문진은 협력 한의원에서 받으실 수 있어요.
          </span>
        </button>

        <p className="pt-md text-center text-caption text-faint">
          본 정보는 참고용이며 진단이 아닙니다.
        </p>
      </div>
      </>
  )
      }}
    </DataScreen>
  )
}

/** 상단 여정 스텝퍼. 마지막 정거장만 크게 그려 "저기까지 간다"를 미리 보여준다. */
function JourneyStepper() {
  return (
    <div className="flex items-center pt-sm">
      {STATIONS.map((station, index) => {
        const goal = index === STATIONS.length - 1
        return (
          <Fragment key={station.key}>
            {index > 0 ? (
              <span
                className={[
                  'mb-lg h-[3px] flex-1 rounded-pill bg-linear-to-r',
                  goal ? 'from-green-200 to-green-600' : 'from-green-100 to-green-200',
                ].join(' ')}
              />
            ) : null}
            <div className="flex shrink-0 flex-col items-center gap-xs">
              <span
                className={
                  goal
                    ? 'flex h-[56px] w-[56px] items-center justify-center rounded-pill bg-linear-to-br from-green-500 to-green-700 text-title shadow-lg'
                    : 'flex h-[40px] w-[40px] items-center justify-center rounded-pill border-2 border-green-100 bg-surface text-subtitle'
                }
              >
                {station.icon}
              </span>
              <small
                className={
                  goal
                    ? 'text-caption font-extrabold text-primary-dark'
                    : 'text-caption font-bold text-muted'
                }
              >
                {station.label}
              </small>
            </div>
          </Fragment>
        )
      })}
    </div>
  )
}

/** 정거장 하나 = 왼쪽 노드 + 흰 카드. */
function Stage({
  icon,
  title,
  sub,
  lead,
  children,
}: {
  icon: string
  title: string
  sub: string
  lead: string
  children: ReactNode
}) {
  return (
    <div className="relative mb-md">
      <span
        aria-hidden
        className="absolute -left-[33px] top-xs flex h-[32px] w-[32px] items-center justify-center rounded-pill border-2 border-green-200 bg-surface text-hint"
      >
        {icon}
      </span>
      <div className="flex flex-col rounded-lg border border-border bg-surface p-md">
        <h2 className="text-subtitle font-extrabold">
          {title}
          <small className="ml-xs text-caption font-semibold text-faint">{sub}</small>
        </h2>
        <p className="mb-sm mt-[2px] text-caption text-muted">{lead}</p>
        {children}
      </div>
    </div>
  )
}

/** 약점 태그가 붙은 콘텐츠가 아직 없는 정거장. 빈 카드를 그대로 두면 고장으로 보인다. */
function Empty() {
  return <p className="text-caption text-faint">이 체질에 맞는 항목을 준비하고 있어요.</p>
}
