// 문진 문항의 "형식(계약)". docs/06_decisions.md #24.
//
// 문항 내용은 준차트(외부)에서 받는다 — 우리가 만드는 것이 아니다. 하지만 스펙을
// 기다리며 M2를 멈추지 않기 위해, **우리가 형식을 먼저 정의하고** 명백한 더미로
// 화면을 완성한다. 준차트 스펙이 오면 core/survey/provider.ts의 변환 함수 하나만
// 끼우고 fixture(dummy-questions.json)를 교체한다. 화면 코드는 손대지 않는다.

/**
 * single — 다중택일(라디오). 하나만 고른다.
 * multi  — 다지선다(체크박스). 여러 개 고를 수 있다.
 * slider — 슬라이더. 3~5개 중단점 중 하나를 고른다. 저장되는 값은 single과 같다
 *          (중단점 하나의 id). 다른 건 그리는 방식뿐이다.
 *
 * single/multi는 명세서 v5 sc_009 UI요소 3번, slider는 화면설계서 PPT에서 채택(#25).
 */
export type QuestionType = 'single' | 'multi' | 'slider'

export interface QuestionOption {
  id: string
  label: string
}

export interface Question {
  id: string
  /** 1부터. 진행률 표시와 정렬에 쓴다. */
  order: number
  text: string
  type: QuestionType
  /** slider도 중단점을 options로 표현한다 — 왼쪽부터 순서대로 3~5개. */
  options: QuestionOption[]
}

export interface Questionnaire {
  id: string
  title: string
  description: string
  estimatedMinutes: number
  /** 'dummy' | 'junchart'. 화면에 더미임을 표시할지 판단하는 데 쓴다. */
  source: 'dummy' | 'junchart'
  questions: Question[]
}

/**
 * 한 문항의 응답. slider·single은 optionIds 길이가 1이다.
 *
 * ★ slider는 `value`(중단점 번호, 1부터인 정수)를 함께 갖는다. 화면만 슬라이더이고
 *   판별 쪽으로 넘어가는 값은 int다. optionIds도 같이 두는 이유는 "다시 들어왔을 때
 *   어느 점이 켜져 있었나"를 화면이 복원해야 하기 때문이다.
 */
export interface Answer {
  questionId: string
  optionIds: string[]
  value?: number
}

/** 판별 API(`POST /api/diagnosis/run/`)에 넘기는 형태. */
export type DiagnosisAnswer =
  | { questionId: string; value: number }
  | { questionId: string; optionIds: string[] }

export function toDiagnosisAnswers(answers: Answer[]): DiagnosisAnswer[] {
  return answers.map((a) =>
    // 슬라이더는 지문 id가 아니라 중단점 번호(int)로 넘긴다.
    a.value !== undefined
      ? { questionId: a.questionId, value: a.value }
      : { questionId: a.questionId, optionIds: a.optionIds },
  )
}

export function isAnswered(answer: Answer | undefined): boolean {
  return !!answer && answer.optionIds.length > 0
}
