// 최소 API 클라이언트. 세션 쿠키 인증이라 credentials: 'include'가 핵심이다.
// docs/08_tech_stack.md §3.
export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`, { credentials: 'include' })
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json() as Promise<T>
}
