// 문항 공급자 — 준차트 연동의 경계선. docs/06_decisions.md #24.
//
// 지금은 더미 fixture를 그대로 돌려준다. 준차트 스펙이 오면 여기서 할 일은 둘뿐이다.
//   1) fetchQuestionnaire()가 준차트 API를 부르게 바꾼다
//   2) 준차트 응답 → Questionnaire 변환 함수를 아래에 하나 추가한다
// 화면(ui/screens/survey/*)은 Questionnaire 타입만 알므로 손대지 않는다.
//
// 판별 어댑터(backend/apps/diagnosis/providers.py)와 같은 발상이다 — 외부 시스템의
// 존재를 그 결과를 쓰는 코드가 알면 안 된다.

import dummyQuestions from './dummy-questions.json'
import type { Questionnaire } from './types'

// 더미는 **유형별 1문항씩 3개**만 둔다(single·multi·slider). 문항 수를 늘려도
// 확인되는 건 같은 화면의 반복뿐이고, 화면을 훑어보는 동안 30번을 눌러야 하는 쪽이
// 훨씬 비싸다. 실제 문항 수(30~40)는 준차트가 정한다 — 우리가 정할 값이 아니다.

/** 지연 시뮬레이션 없이 즉시 돌려준다 — 문항 로딩은 판별과 달리 느릴 이유가 없다. */
export async function fetchQuestionnaire(): Promise<Questionnaire> {
  return dummyQuestions as Questionnaire
}

// ── 준차트 연동 시 여기에 변환 함수를 추가한다 ───────────────────────
// export function fromJunchart(payload: JunchartQuestionsResponse): Questionnaire { ... }
