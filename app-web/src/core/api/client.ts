// 플랫폼 무관 API 클라이언트. core/에 둔다 — RN 전환 시 그대로 넘어간다.
// docs/08_tech_stack.md §7.
//
// 세션 쿠키 인증이라 credentials: 'include'가 핵심이다(§3). 비GET 요청은 Django의
// CSRF 보호를 통과해야 하므로 csrftoken 쿠키 값을 X-CSRFToken 헤더로 실어 보낸다.
//
// ★ document.cookie는 웹 전용이라 §7-3에 따라 얇은 어댑터(core/platform/cookie.ts)
//   뒤에 두었다. RN에서는 그 파일 하나만 갈아끼우면 된다.
import { readCookie } from '../platform/cookie'

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(`API 요청 실패: ${status}`)
    this.status = status
    this.detail = detail
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET') {
    const csrfToken = readCookie('csrftoken')
    if (csrfToken) headers['X-CSRFToken'] = csrfToken
  }

  const res = await fetch(`/api${path}`, {
    method,
    credentials: 'include',
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const apiGet = <T,>(path: string) => request<T>('GET', path)
export const apiPost = <T,>(path: string, body?: unknown) => request<T>('POST', path, body)
export const apiPatch = <T,>(path: string, body?: unknown) => request<T>('PATCH', path, body)
export const apiDelete = (path: string) => request<void>('DELETE', path)
