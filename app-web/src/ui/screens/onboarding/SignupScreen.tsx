import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router'

import { saveDiagnosis } from '../../../core/api/diagnosis'
import { useAuthStore } from '../../../core/store/auth'
import { useSurveyStore } from '../../../core/store/survey'
import { Button } from '../../components/Button'
import { Field, TextInput } from '../../components/Form'
import { Screen } from '../../components/Screen'
import { TopBar } from '../../components/TopBar'
import { ROUTES } from '../../routes'

// sc_091 로그인 — 실제로는 "가입 또는 로그인"을 겸한다.
//
// 1차 로그인 수단은 **이메일**이다(docs/06_decisions.md #23). 명세서 v5는 카카오 단독을
// 전제했지만, 카카오에서 이메일 같은 개인정보를 받으려면 비즈앱 전환이 선행돼야 하고
// 그 일정이 외부에 달려 있다. 카카오는 backend의 AuthProvider 어댑터에 자리만 잡아 뒀고,
// 준비되면 이 화면에 버튼 한 줄이 늘어난다.
//
// ★ 가입 모드에서는 여기서 서버를 부르지 않는다. 이메일·비밀번호를 들고 sc_092로
//   넘어가서, **동의까지 받은 다음에 한 번에** 전송한다 — 동의 없이 이메일부터
//   저장되는 상태를 만들지 않기 위함이다(docs/02_architecture_constraints.md §4).

export function SignupScreen() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((s) => s.login)
  const error = useAuthStore((s) => s.error)
  const rawValue = useSurveyStore((s) => s.rawValue)
  const clearSurvey = useSurveyStore((s) => s.clear)

  // 문진 유도(sc_004a)에서 '이미 계정이 있어요'로 들어오면 바로 로그인 모드로 연다.
  // 앱을 직접 켠 기존 회원이 가입 폼부터 만나면 "또 가입해야 하나" 싶어진다.
  const initialMode = (location.state as { mode?: 'signup' | 'login' } | null)?.mode ?? 'signup'
  const [mode, setMode] = useState<'signup' | 'login'>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  const canSubmit = email.includes('@') && password.length >= 8 && !busy

  async function handleSubmit() {
    if (mode === 'signup') {
      navigate(ROUTES.consent, { state: { email, password } })
      return
    }
    setBusy(true)
    try {
      await login(email, password)

      // 방금 문진을 풀고 들어온 기존 회원이면 그 결과부터 저장한다.
      // 이게 없으면 "문진 → 티저 → 로그인" 경로에서 방금 푼 결과가 통째로 사라지고
      // 예전 결과(또는 결과 없음)가 보인다.
      if (rawValue !== null) {
        await saveDiagnosis(rawValue)
        clearSurvey()
        navigate(ROUTES.result, { replace: true })
        return
      }
      // 그냥 로그인만 하러 온 재방문자는 홈으로 — 문진 여부에 따라 홈이 알아서 갈린다.
      navigate(ROUTES.home, { replace: true })
    } catch {
      // 문구는 store가 error에 담아 둔다.
    } finally {
      setBusy(false)
    }
  }

  return (
    <Screen
      header={<TopBar />}
      footer={
        <>
          <Button disabled={!canSubmit} onClick={handleSubmit}>
            {mode === 'signup' ? '다음' : '로그인'}
          </Button>
          <Button variant="text" onClick={() => setMode(mode === 'signup' ? 'login' : 'signup')}>
            {mode === 'signup' ? '이미 계정이 있어요' : '처음이신가요? 가입하기'}
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-lg pb-lg">
        <div className="flex flex-col gap-sm">
          <h1 className="text-title font-extrabold leading-snug">
            {mode === 'signup' ? (
              <>
                결과를 저장하려면
                <br />
                가입이 필요해요
              </>
            ) : (
              '다시 오셨네요'
            )}
          </h1>
          <p className="text-body text-muted">
            {mode === 'signup'
              ? '이메일로 간편하게 시작할 수 있어요.'
              : '가입하실 때 쓴 이메일로 로그인해주세요.'}
          </p>
        </div>

        <div className="flex flex-col gap-md">
          <Field label="이메일">
            <TextInput type="email" value={email} onChange={setEmail} autoComplete="email" placeholder="you@example.com" />
          </Field>
          <Field label="비밀번호" hint="8자 이상으로 지어주세요.">
            <TextInput
              type="password"
              value={password}
              onChange={setPassword}
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            />
          </Field>
        </div>

        {error ? <p className="text-hint text-danger">{error}</p> : null}
      </div>
    </Screen>
  )
}
