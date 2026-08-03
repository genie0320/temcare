import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'

import { DiagnosisError, runDiagnosis, type DiagnosisFailure } from '../../../core/api/diagnosis'
import { useSurveyStore } from '../../../core/store/survey'
import { Button } from '../../components/Button'
import { Screen } from '../../components/Screen'
import { ROUTES } from '../../routes'

// sc_009a 결과 대기 — 판별 API 응답 대기 + 지연·실패·타임아웃 재시도 UI.
//
// 1차는 mock 판별이지만 **실패 경로를 실제로 재현해서 검증한다**(docs/07_milestones.md M2).
// 쿼리스트링으로 강제할 수 있다:
//   /survey/waiting?fail=1     실패(502)
//   /survey/waiting?timeout=1  타임아웃(504)
//   /survey/waiting?delay=3    3초 지연
// 준차트 실연동 후에도 이 화면은 그대로 쓴다 — 어댑터가 같은 모양의 오류를 던진다.

const FAILURE_COPY: Record<DiagnosisFailure, { title: string; body: string }> = {
  timeout: {
    title: '분석이 조금 오래 걸리고 있어요',
    body: '잠시 후 다시 시도하면 대부분 바로 끝나요.',
  },
  failed: {
    title: '분석을 마치지 못했어요',
    body: '답변은 그대로 남아 있으니 다시 시도해주세요.',
  },
  network: {
    title: '연결이 끊겼어요',
    body: '네트워크 상태를 확인하고 다시 시도해주세요.',
  },
}

export function SurveyWaitingScreen() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const answers = useSurveyStore((s) => s.answers)
  const setRawValue = useSurveyStore((s) => s.setRawValue)

  const [failure, setFailure] = useState<DiagnosisFailure | null>(null)
  const [attempt, setAttempt] = useState(0)

  const run = useCallback(async () => {
    setFailure(null)
    try {
      const raw = await runDiagnosis(answers, {
        delaySeconds: Number(params.get('delay') ?? 0),
        forceFail: params.get('fail') === '1',
        forceTimeout: params.get('timeout') === '1',
      })
      setRawValue(raw)
      navigate(ROUTES.resultTeaser, { replace: true })
    } catch (err) {
      setFailure(err instanceof DiagnosisError ? err.kind : 'network')
    }
  }, [answers, navigate, params, setRawValue])

  useEffect(() => {
    void run()
  }, [run, attempt])

  if (failure) {
    const copy = FAILURE_COPY[failure]
    return (
      <Screen
        center
        footer={
          <>
            <Button onClick={() => setAttempt((n) => n + 1)}>다시 시도하기</Button>
            <Button variant="text" onClick={() => navigate(ROUTES.survey)}>
              답변 다시 보기
            </Button>
          </>
        }
      >
        <div className="flex flex-col items-center gap-md text-center">
          <span className="text-hero">😥</span>
          <h1 className="text-title font-extrabold">{copy.title}</h1>
          <p className="text-body text-muted">{copy.body}</p>
        </div>
      </Screen>
    )
  }

  return (
    <Screen center>
      <div className="flex flex-col items-center gap-md text-center">
        {/* 로고가 차오르는 애니메이션(PPT LOADING-01 #1)의 자리. 지금은 맥박으로 대신한다. */}
        <div className="flex h-[96px] w-[96px] animate-pulse items-center justify-center rounded-xl bg-primary text-hero font-bold text-white">
          올라
        </div>
        <h1 className="text-title font-extrabold">체질을 분석하고 있어요</h1>
        <p className="text-body text-muted">잠시만 기다려주세요…</p>
      </div>
    </Screen>
  )
}
