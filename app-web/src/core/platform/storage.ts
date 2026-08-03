// 웹 전용 API를 감싸는 얇은 어댑터. docs/08_tech_stack.md §7-3.
// RN 전환 시 AsyncStorage로 이 파일만 갈아끼운다.
//
// ★ 인증 토큰을 여기 넣지 않는다. 인증은 HttpOnly 세션 쿠키다(§3 · docs/02 §5).
//   여기 담기는 것은 "가입 전 임시 보관"용 문진 진행 상태뿐이며, 가입이 끝나면 지운다.

export function loadJSON<T>(key: string): T | null {
  try {
    const raw = window.sessionStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    // 사파리 프라이빗 모드 등 저장소가 막힌 환경 — 기능은 살고 새로고침 복원만 포기한다.
    return null
  }
}

export function saveJSON(key: string, value: unknown): void {
  try {
    window.sessionStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* 위와 동일 */
  }
}

export function removeKey(key: string): void {
  try {
    window.sessionStorage.removeItem(key)
  } catch {
    /* 위와 동일 */
  }
}
