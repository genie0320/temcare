import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useAuthStore } from '../store/auth'

export function LoginPage() {
  const [email, setEmail] = useState('admin@ollacare.local')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { error, loginWithPassword, devLogin } = useAuthStore()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await loginWithPassword(email, password)
      navigate('/content/weaknesses')
    } catch {
      // 에러 메시지는 store.error로 노출된다.
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDevLogin() {
    setSubmitting(true)
    try {
      await devLogin()
      navigate('/content/weaknesses')
    } catch {
      // 에러 메시지는 store.error로 노출된다.
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1>올라케어 관리자</h1>
        <p>이메일과 비밀번호로 로그인한다.</p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="email">이메일</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ maxWidth: '100%' }} />
          <label htmlFor="password">비밀번호</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ maxWidth: '100%' }}
          />
          {error && <p className="err">{error}</p>}
          <button className="btn primary" type="submit" disabled={submitting} style={{ width: '100%', marginTop: 18, justifyContent: 'center' }}>
            로그인
          </button>
        </form>
        <button
          className="btn ghost"
          onClick={handleDevLogin}
          disabled={submitting}
          style={{ width: '100%', marginTop: 10, justifyContent: 'center' }}
        >
          개발용 빠른 로그인
        </button>
      </div>
    </div>
  )
}
