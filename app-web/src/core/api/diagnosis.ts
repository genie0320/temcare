// 판별 API. 백엔드가 이미 어댑터(mock ↔ 준차트) 뒤에 있으므로 프론트는
// "raw 정수 하나를 받는다"만 안다. docs/02_architecture_constraints.md §3.

import { toDiagnosisAnswers, type Answer } from '../survey/types'
import { ApiError, apiPost } from './client'

export type DiagnosisFailure = 'timeout' | 'failed' | 'network'

export interface RunOptions {
  /** 개발·시연용 강제 분기. sc_009a의 재시도 UI를 실제 장애 없이 확인하려고 쓴다. */
  delaySeconds?: number
  forceFail?: boolean
  forceTimeout?: boolean
}

export class DiagnosisError extends Error {
  kind: DiagnosisFailure

  constructor(kind: DiagnosisFailure) {
    super(`diagnosis ${kind}`)
    this.kind = kind
  }
}

/** 비로그인 상태로 호출 가능하다(백엔드 run_diagnosis가 AllowAny). */
export async function runDiagnosis(answers: Answer[], options: RunOptions = {}): Promise<number> {
  try {
    const res = await apiPost<{ raw: number; status: string }>('/diagnosis/run/', {
      answers: toDiagnosisAnswers(answers),
      delay_seconds: options.delaySeconds ?? 0,
      force_fail: options.forceFail ?? false,
      force_timeout: options.forceTimeout ?? false,
    })
    return res.raw
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 504) throw new DiagnosisError('timeout')
      if (err.status === 502) throw new DiagnosisError('failed')
    }
    throw new DiagnosisError('network')
  }
}

/** 가입 완료 직후 호출한다 — 여기서 처음 diagnosis_result가 만들어진다(§6). */
export async function saveDiagnosis(raw: number): Promise<void> {
  await apiPost('/diagnosis/save/', { raw, provider: 'mock' })
}
