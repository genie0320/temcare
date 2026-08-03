import { ROUTES } from '../routes'

// 결과 화면(sc_004b)과 처방 화면(sc_007)이 **똑같이** 갖고 있는 두 개의 문.
//
//   ① 아직 문진을 안 했다                       → 문진으로 보낸다
//   ② 문진은 했는데 그 체질의 콘텐츠가 아직 없다 → 개발용 안내
//
// 두 화면에 각각 복사돼 있던 것을 여기로 모았다. 문구가 갈라지면 같은 상황인데
// 화면마다 다른 말을 하게 된다.
//
// ★ '실패'는 여기 없다 — 그건 DataScreen이 맡는다. 둘을 섞으면 다시 "실패 = 없음"이 된다.
//
// ★ JSX가 아니라 **설명값(descriptor)** 을 돌려준다. 화면 본문은 DataScreen의
//   render prop 안에서 그려지는데, 거기서 훅(useNavigate 등)을 부르면 분기에 따라
//   훅 호출 순서가 달라져 React 규칙을 깬다. 순수 함수면 그 위험이 아예 없다.

export interface GateNotice {
  message: string
  tone: 'muted' | 'warn'
  action?: { label: string; to: string }
}

interface Gated {
  hasResult: boolean
  found?: boolean
  typeId?: string
}

/** 막아야 할 상황이면 안내를, 통과할 상황이면 null. */
export function resultGate(data: Gated): GateNotice | null {
  if (!data.hasResult) {
    return {
      message: '아직 문진 결과가 없어요.',
      tone: 'muted',
      action: { label: '문진 시작하기', to: ROUTES.surveyIntro },
    }
  }

  if (!data.found) {
    // 개발 중에만 보이는 상태 — tem_type 시드가 아직 전부 차 있지 않다.
    return {
      message: `${data.typeId} — 이 체질의 콘텐츠가 아직 없어요. (개발용 시드 미완성)`,
      tone: 'warn',
    }
  }

  return null
}
