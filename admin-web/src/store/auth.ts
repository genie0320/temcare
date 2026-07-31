import { create } from 'zustand'
import { apiGet, apiPost } from '../api/client'

interface AdminUser {
  id: number
  email: string
  username: string
  role: string | null
}

interface MeResponse {
  authenticated: boolean
  id?: number
  email?: string
  username?: string
  role?: string | null
}

type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

interface AuthState {
  status: AuthStatus
  user: AdminUser | null
  error: string | null
  bootstrap: () => Promise<void>
  loginWithPassword: (email: string, password: string) => Promise<void>
  devLogin: () => Promise<void>
  logout: () => Promise<void>
}

function toUser(res: MeResponse): AdminUser | null {
  if (!res.authenticated) return null
  return { id: res.id!, email: res.email!, username: res.username!, role: res.role ?? null }
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'loading',
  user: null,
  error: null,

  bootstrap: async () => {
    await apiGet('/accounts/csrf/') // csrftoken 쿠키를 먼저 심는다
    const res = await apiGet<MeResponse>('/accounts/me/')
    const user = toUser(res)
    set({ status: user ? 'authenticated' : 'anonymous', user })
  },

  loginWithPassword: async (email, password) => {
    set({ error: null })
    try {
      const res = await apiPost<MeResponse>('/accounts/login/', { email, password })
      set({ status: 'authenticated', user: toUser(res) })
    } catch {
      set({ error: '이메일 또는 비밀번호가 올바르지 않다.' })
      throw new Error('login failed')
    }
  },

  devLogin: async () => {
    set({ error: null })
    try {
      const res = await apiPost<MeResponse>('/accounts/dev-login/')
      set({ status: 'authenticated', user: toUser(res) })
    } catch {
      set({ error: '빠른 로그인을 쓸 수 없다(DEBUG 모드 전용).' })
      throw new Error('dev login failed')
    }
  },

  logout: async () => {
    await apiPost('/accounts/logout/')
    set({ status: 'anonymous', user: null })
  },
}))
