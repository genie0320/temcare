// 비로그인 문진 상태. docs/02_architecture_constraints.md §4·§6, docs/06_decisions.md #13.
//
// ★ 여기 담기는 것은 전부 **서버에 보내기 전** 데이터다. 동의 없이 개인정보를 먼저
//   모아두지 않기 위해, 문진 응답·생년월일·성별·판별 결과(raw)를 가입이 끝날 때까지
//   클라이언트에만 들고 있다가 한 번에 전송한다.
// ★ 가입이 끝나면 clear()로 반드시 지운다 — 브라우저에 남겨둘 이유가 없다.

import { create } from 'zustand'

import { loadJSON, removeKey, saveJSON } from '../platform/storage'
import type { Answer } from '../survey/types'

const STORAGE_KEY = 'ollacare.survey.draft'

export type Gender = '남성' | '여성'

export interface SurveyProfile {
  birthDate: string // 'YYYY-MM-DD'
  gender: Gender | ''
  /** 화면설계서 '홈 > TEM문진' #3·#4. 비워둘 수 있다. */
  heightCm: string
  weightKg: string
}

interface SurveyDraft extends SurveyProfile {
  answers: Answer[]
  /** 판별 결과 1~64. 아직 안 받았으면 null. */
  rawValue: number | null
}

const EMPTY: SurveyDraft = {
  birthDate: '',
  gender: '',
  heightCm: '',
  weightKg: '',
  answers: [],
  rawValue: null,
}

interface SurveyState extends SurveyDraft {
  setProfile: (profile: SurveyProfile) => void
  /** value는 슬라이더 전용 — 중단점 번호(1부터인 정수). 나머지 유형은 넘기지 않는다. */
  setAnswer: (questionId: string, optionIds: string[], value?: number) => void
  answerFor: (questionId: string) => Answer | undefined
  setRawValue: (raw: number) => void
  clear: () => void
}

export const useSurveyStore = create<SurveyState>((set, get) => {
  /** 바뀐 것만 넘기면 나머지는 현재 상태에서 읽어 통째로 저장한다.
   *  필드를 하나 늘릴 때마다 저장 코드 세 군데를 같이 고치던 것을 없앴다. */
  function commit(patch: Partial<SurveyDraft>) {
    set(patch)
    const { birthDate, gender, heightCm, weightKg, answers, rawValue } = get()
    saveJSON(STORAGE_KEY, { birthDate, gender, heightCm, weightKg, answers, rawValue })
  }

  return {
    // 새로고침해도 진행 중이던 문진이 날아가지 않게 복원한다(명세서 sc_009 "이탈 시 임시저장").
    // 저장된 초안에 없는 필드(나중에 늘어난 것)는 EMPTY 기본값으로 메운다.
    ...EMPTY,
    ...(loadJSON<SurveyDraft>(STORAGE_KEY) ?? {}),

    setProfile: (profile) => commit(profile),

    setAnswer: (questionId, optionIds, value) => {
      const answers = get().answers.filter((a) => a.questionId !== questionId)
      if (optionIds.length > 0) {
        answers.push({ questionId, optionIds, ...(value === undefined ? {} : { value }) })
      }
      commit({ answers })
    },

    answerFor: (questionId) => get().answers.find((a) => a.questionId === questionId),

    setRawValue: (rawValue) => commit({ rawValue }),

    clear: () => {
      set({ ...EMPTY })
      removeKey(STORAGE_KEY)
    },
  }
})
