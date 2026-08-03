// 웹 전용 API를 감싸는 얇은 어댑터. docs/08_tech_stack.md §7-3.
// 화면 코드는 document를 직접 부르지 않는다 — RN 전환 시 이 파일만 갈아끼운다.

export function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}
