// 고객 인증 상태. 백엔드는 /api/auth/*(apps/accounts/customer_views.py).
// 관리자(/api/accounts/*)와 경로가 다르다 — 같은 User 모델이지만 성격이 다르기 때문.
//
// ★ 토큰을 브라우저 저장소에 넣지 않는다. 인증은 HttpOnly 세션 쿠키다
//   (docs/08_tech_stack.md §3). 여기 있는 건 화면에 뿌릴 사용자 정보뿐이다.

import { create } from 'zustand'

import { apiGet, ApiError, apiPatch, apiPost } from '../api/client'
import type { Gender } from './survey'

export interface CustomerUser {
  id: number
  email: string
  nickname: string
  status: string
  birthDate: string | null
  gender: string
  heightCm: number | null
  weightKg: number | null
}

interface MeResponse extends Partial<CustomerUser> {
  authenticated: boolean
}

export interface SignupPayload {
  email: string
  password: string
  /** 동의한 항목 id 목록. 필수 항목이 빠지면 서버가 400으로 막는다. */
  consents: string[]
  birthDate?: string
  gender?: Gender | ''
  /** 빈 문자열이면 보내지 않는다 — 서버가 "없음"과 "잘못된 값"을 구분해야 한다. */
  heightCm?: string
  weightKg?: string
}

type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

interface AuthState {
  status: AuthStatus
  user: CustomerUser | null
  error: string | null
  bootstrap: () => Promise<void>
  signup: (payload: SignupPayload) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  updateNickname: (nickname: string) => Promise<void>
  logout: () => Promise<void>
}

function toUser(res: MeResponse): CustomerUser | null {
  if (!res.authenticated) return null
  return {
    id: res.id!,
    email: res.email ?? '',
    nickname: res.nickname ?? '',
    status: res.status ?? '정상',
    birthDate: res.birthDate ?? null,
    gender: res.gender ?? '',
    heightCm: res.heightCm ?? null,
    weightKg: res.weightKg ?? null,
  }
}

/** 서버가 내려준 문구를 그대로 보여준다 — 화면마다 다시 쓰면 문구가 갈린다. */
function messageOf(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.detail && typeof err.detail === 'object') {
    const detail = (err.detail as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

/** 서버가 붙여 보낸 오류 코드. 문구가 아니라 코드로 분기해야 문구를 고쳐도 안 깨진다. */
function codeOf(err: unknown): string | null {
  if (err instanceof ApiError && err.detail && typeof err.detail === 'object') {
    const code = (err.detail as { code?: unknown }).code
    if (typeof code === 'string') return code
  }
  return null
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'loading',
  user: null,
  error: null,

  bootstrap: async () => {
    await apiGet('/auth/csrf/') // csrftoken 쿠키를 먼저 심는다
    const res = await apiGet<MeResponse>('/auth/me/')
    const user = toUser(res)
    set({ status: user ? 'authenticated' : 'anonymous', user })
  },

  signup: async (payload) => {
    set({ error: null })
    try {
      const res = await apiPost<MeResponse>('/auth/signup/', payload)
      set({ status: 'authenticated', user: toUser(res) })
    } catch (err) {
      // 이미 세션이 있는 사람이 가입 화면까지 온 경우(409). 서버가 막는 것은 맞지만
      // 화면까지 막히면 **결과를 영영 못 보는 막다른 길**이 된다 — 실제로 여기서
      // 걸렸다. 만들려던 계정이 이미 있으니 그 계정으로 계속 간다. 동의도 그 계정을
      // 만들 때 이미 받아 두었다.
      if (codeOf(err) === 'already_logged_in') {
        const me = await apiGet<MeResponse>('/auth/me/')
        set({ status: 'authenticated', user: toUser(me), error: null })
        return
      }
      set({ error: messageOf(err, '가입에 실패했어요. 잠시 후 다시 시도해주세요.') })
      throw err
    }
  },

  login: async (email, password) => {
    set({ error: null })
    try {
      const res = await apiPost<MeResponse>('/auth/login/', { email, password })
      set({ status: 'authenticated', user: toUser(res) })
    } catch (err) {
      set({ error: messageOf(err, '이메일 또는 비밀번호가 올바르지 않아요.') })
      throw err
    }
  },

  updateNickname: async (nickname) => {
    set({ error: null })
    try {
      const res = await apiPatch<MeResponse>('/auth/me/', { nickname })
      set({ user: toUser(res) })
    } catch (err) {
      set({ error: messageOf(err, '닉네임을 저장하지 못했어요.') })
      throw err
    }
  },

  logout: async () => {
    await apiPost('/auth/logout/')
    set({ status: 'anonymous', user: null })
  },
}))
