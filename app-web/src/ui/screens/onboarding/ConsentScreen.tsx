import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { fetchConsentItems, fetchTerms } from '../../../core/api/consent'
import { saveDiagnosis } from '../../../core/api/diagnosis'
import { useAuthStore } from '../../../core/store/auth'
import { useSurveyStore } from '../../../core/store/survey'
import { Button } from '../../components/Button'
import { CheckRow } from '../../components/Form'
import { Screen } from '../../components/Screen'
import { TopBar } from '../../components/TopBar'
import { ROUTES } from '../../routes'

// sc_092 약관 동의 — **이 마일스톤의 핵심**(docs/07_milestones.md M2).
//
// 지켜야 하는 것
// - 민감정보(건강정보) 동의는 일반 개인정보 동의와 **별도 체크박스**여야 한다(제23조).
//   서버가 is_sensitive로 알려주므로 화면은 그걸 그대로 반영한다.
// - 만 14세 확인은 자기신고. 미충족이면 가입 불가.
// - 마케팅 수신 동의는 **선택**이며, 거절해도 서비스를 쓸 수 있어야 한다.
//   발송 수단은 2차지만 동의는 지금 받아둔다(결정 #12) — 나중에 받으려면 재동의
//   캠페인을 돌려야 해서 훨씬 비싸다.
// - 전체 동의 체크박스는 **기본 미체크**다(사전 체크 금지).
//
// 여기서 실제 가입(POST /api/auth/signup/)이 일어난다. 이유는 SignupScreen 주석 참고.

interface SignupState {
  email?: string
  password?: string
}

export function ConsentScreen() {
  const navigate = useNavigate()
  const location = useLocation()
  const { email, password } = (location.state ?? {}) as SignupState

  const signup = useAuthStore((s) => s.signup)
  const authError = useAuthStore((s) => s.error)
  const birthDate = useSurveyStore((s) => s.birthDate)
  const heightCm = useSurveyStore((s) => s.heightCm)
  const weightKg = useSurveyStore((s) => s.weightKg)
  const gender = useSurveyStore((s) => s.gender)
  const rawValue = useSurveyStore((s) => s.rawValue)
  const clearSurvey = useSurveyStore((s) => s.clear)

  const [agreed, setAgreed] = useState<string[]>([])
  const [viewing, setViewing] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const { data: items = [] } = useQuery({ queryKey: ['consent-items'], queryFn: fetchConsentItems })
  const { data: terms } = useQuery({
    queryKey: ['terms', viewing],
    queryFn: () => fetchTerms(viewing!),
    enabled: viewing !== null,
  })

  const requiredIds = items.filter((i) => i.required).map((i) => i.id)
  const allRequiredAgreed = requiredIds.length > 0 && requiredIds.every((id) => agreed.includes(id))
  const allAgreed = items.length > 0 && items.every((i) => agreed.includes(i.id))

  function toggle(id: string) {
    setAgreed((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  function toggleAll() {
    setAgreed(allAgreed ? [] : items.map((i) => i.id))
  }

  async function handleSubmit() {
    if (!email || !password) {
      // 가입 정보 없이 URL로 직접 들어온 경우.
      navigate(ROUTES.signup, { replace: true })
      return
    }
    setBusy(true)
    try {
      await signup({ email, password, consents: agreed, birthDate, gender, heightCm, weightKg })
      // 가입이 끝난 지금이 문진 결과를 서버에 처음 올리는 시점이다(§6).
      if (rawValue !== null) await saveDiagnosis(rawValue)
      clearSurvey() // 브라우저에 남겨둘 이유가 없다
      navigate(ROUTES.nickname, { replace: true })
    } catch {
      // 문구는 store가 error에 담아 둔다.
    } finally {
      setBusy(false)
    }
  }

  if (viewing) {
    return (
      <Screen header={<TopBar title={terms?.documentName ?? '약관'} onBack={() => setViewing(null)} />}>
        <div className="flex flex-col gap-sm pb-lg">
          {terms ? (
            <>
              <p className="text-caption text-faint">
                {terms.version} · 시행일 {terms.effectiveAt}
              </p>
              <p className="whitespace-pre-wrap text-body leading-relaxed">{terms.body}</p>
            </>
          ) : (
            <p className="text-body text-muted">불러오는 중…</p>
          )}
        </div>
      </Screen>
    )
  }

  return (
    <Screen
      header={<TopBar />}
      footer={
        <Button disabled={!allRequiredAgreed || busy} onClick={handleSubmit}>
          네, 모두 동의해요
        </Button>
      }
    >
      <div className="flex flex-col gap-lg pb-lg">
        <h1 className="text-title font-extrabold leading-snug">
          서비스 이용을 위해
          <br />
          동의가 필요해요
        </h1>

        <div className="flex flex-col rounded-md bg-surface px-md py-sm">
          <CheckRow checked={allAgreed} onToggle={toggleAll} label="전체 동의하기" strong />
          <div className="my-xs h-px bg-border" />
          {items.map((item) => (
            <CheckRow
              key={item.id}
              checked={agreed.includes(item.id)}
              onToggle={() => toggle(item.id)}
              label={item.name}
              badge={item.required ? '[필수]' : '[선택]'}
              onView={item.documentId ? () => setViewing(item.documentId!) : undefined}
            />
          ))}
        </div>

        <p className="text-caption leading-relaxed text-faint">
          건강정보는 민감정보라 다른 항목과 따로 동의를 받고 있어요. 선택 항목에 동의하지
          않으셔도 서비스를 이용하실 수 있습니다.
        </p>

        {authError ? <p className="text-hint text-danger">{authError}</p> : null}
      </div>
    </Screen>
  )
}
