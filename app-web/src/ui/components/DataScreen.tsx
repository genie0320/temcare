import type { ReactNode } from 'react'
import { useNavigate } from 'react-router'
import type { UseQueryResult } from '@tanstack/react-query'

import { Button } from './Button'
import { Screen } from './Screen'
import { TopBar } from './TopBar'
import type { GateNotice } from './ResultGate'

// 데이터를 불러와서 그리는 화면의 공통 껍데기.
//
// ★ 이게 없을 때 무슨 일이 있었나 (2026-08-03 리뷰에서 실제로 재현):
//   화면마다 `const { data, isPending } = useQuery(...)`를 각자 쓰면서 **실패한
//   경우를 아무도 받지 않았다.** 실패하면 data가 undefined가 되는데, 그게
//   "정상적으로 비어 있음"과 구분되지 않아서 —
//     · 결과가 있는 회원에게 "아직 문진 결과가 없어요 / 문진 시작하기"가 뜨고
//     · 깔때기의 출구인 협력 한의원 화면에 "준비된 협력 한의원이 아직 없어요"가 떴다.
//   서버가 잠깐 삐끗한 것뿐인데 사용자에게는 **없는 것**으로 보인다. 원장이 다른
//   원장에게 시연하는 자리에서 이게 뜨면 그날 시연은 거기서 끝난다.
//
//   그래서 "불러오는 중 / 실패 / 정상"을 화면마다 손으로 쓰지 않고 여기 한 곳에
//   둔다. 실패에는 반드시 **다시 시도**가 붙는다 — 막다른 길을 만들지 않는다.
//
// 도메인 분기(결과가 없다 / 이 체질 콘텐츠가 아직 없다)는 여기 넣지 않는다.
// 그건 화면마다 뜻이 달라서 ResultGate가 따로 맡는다.

interface DataScreenProps<T> {
  query: UseQueryResult<T>
  children: (data: T) => ReactNode
  /** 상단 바. 주지 않으면 뒤로가기만 있는 기본 TopBar가 붙는다 — 모든 화면의 상단 높이를 같게 유지한다. */
  header?: ReactNode
  footer?: ReactNode
  tabBar?: ReactNode
  bleed?: boolean
  /** 실패 화면에 쓸 안내 문구. 화면마다 무엇을 못 불러왔는지가 다르다. */
  errorLabel?: string
  /**
   * 불러오기는 성공했지만 **본문을 그릴 수 없는 상황**을 알려주는 순수 함수.
   * (예: 아직 문진 전이다 / 이 체질의 콘텐츠가 아직 없다) — ResultGate 참고.
   */
  gate?: (data: T) => GateNotice | null
}

export function DataScreen<T>({
  query,
  children,
  header,
  footer,
  tabBar,
  bleed = false,
  errorLabel = '정보를 불러오지 못했어요.',
  gate,
}: DataScreenProps<T>) {
  const navigate = useNavigate()
  const bar = header ?? <TopBar />

  if (query.isPending) {
    return (
      <Screen header={bar} tabBar={tabBar} center>
        <p className="text-center text-body text-muted">불러오는 중…</p>
      </Screen>
    )
  }

  if (query.isError || query.data === undefined) {
    return (
      <Screen
        header={bar}
        tabBar={tabBar}
        center
        footer={
          <Button variant="ghost" onClick={() => void query.refetch()}>
            다시 시도
          </Button>
        }
      >
        <div className="flex flex-col items-center gap-xs text-center">
          <p className="text-body text-muted">{errorLabel}</p>
          {/* 사용자가 자기 잘못이라고 느끼지 않게 원인을 분명히 말한다. */}
          <p className="text-hint text-faint">잠시 후 다시 시도해 주세요.</p>
        </div>
      </Screen>
    )
  }

  const notice = gate?.(query.data) ?? null
  if (notice) {
    return (
      <Screen
        header={bar}
        tabBar={tabBar}
        center
        footer={
          notice.action ? (
            <Button onClick={() => navigate(notice.action!.to)}>{notice.action.label}</Button>
          ) : undefined
        }
      >
        <p
          className={[
            'text-center',
            notice.tone === 'warn' ? 'text-hint text-orange-500' : 'text-body text-muted',
          ].join(' ')}
        >
          {notice.message}
        </p>
      </Screen>
    )
  }

  return (
    <Screen header={bar} footer={footer} tabBar={tabBar} bleed={bleed}>
      {children(query.data)}
    </Screen>
  )
}
