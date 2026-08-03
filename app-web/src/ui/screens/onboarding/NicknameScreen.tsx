import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import { apiGet } from '../../../core/api/client'
import { useAuthStore } from '../../../core/store/auth'
import { Button } from '../../components/Button'
import { Field, TextInput } from '../../components/Form'
import { Screen } from '../../components/Screen'
import { ROUTES } from '../../routes'

// PPT SIGNUP-02 닉네임 설정 (docs/06_decisions.md #25에서 채택).
//
// 명세서 v5에는 이 화면이 없는데 홈 인사말(sc_101)이 닉네임을 쓰고 있어 구멍이었다.
// 랜덤 조합 한글 4~8자를 제안하고 사용자가 고칠 수 있다. 서버가 가입 시점에 이미
// 하나를 넣어 두므로 이 화면을 건너뛰어도 이름이 비지 않는다.

export function NicknameScreen() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const updateNickname = useAuthStore((s) => s.updateNickname)
  const error = useAuthStore((s) => s.error)

  const [nickname, setNickname] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (user?.nickname) setNickname(user.nickname)
  }, [user?.nickname])

  async function reroll() {
    const res = await apiGet<{ nickname: string }>('/auth/nickname-suggestion/')
    setNickname(res.nickname)
  }

  async function handleSubmit() {
    setBusy(true)
    try {
      await updateNickname(nickname)
      navigate(ROUTES.permissions, { replace: true })
    } catch {
      // 문구는 store가 error에 담아 둔다.
    } finally {
      setBusy(false)
    }
  }

  const valid = nickname.trim().length >= 4 && nickname.trim().length <= 8

  return (
    <Screen
      footer={
        <Button disabled={!valid || busy} onClick={handleSubmit}>
          가입 완료
        </Button>
      }
    >
      <div className="flex flex-1 flex-col justify-center gap-lg py-xl">
        <div className="flex flex-col gap-sm">
          <h1 className="text-title font-extrabold leading-snug">닉네임을 알려주세요</h1>
          <p className="text-body text-muted">마음에 안 드시면 다른 이름으로 바꾸실 수 있어요.</p>
        </div>

        <Field label="닉네임" hint="한글 4~8글자">
          <TextInput value={nickname} onChange={setNickname} maxLength={8} />
        </Field>

        <Button variant="ghost" onClick={reroll}>
          🎲 다른 닉네임 추천받기
        </Button>

        {error ? <p className="text-hint text-danger">{error}</p> : null}
      </div>
    </Screen>
  )
}
