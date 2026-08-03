// 앱 밖으로 나가는 동작(전화·지도·홈페이지)을 감싸는 얇은 어댑터.
// docs/08_tech_stack.md §7-3 — 화면 코드는 window를 직접 부르지 않는다.
// RN에서는 이 파일 하나를 Linking.openURL로 갈아끼운다.

/** tel: 링크. 하이픈·공백을 걷어내야 일부 다이얼러가 번호를 제대로 받는다. */
export function telHref(phone: string): string {
  return `tel:${phone.replace(/[^0-9+]/g, '')}`
}

/**
 * 지도·홈페이지처럼 **우리 도메인 밖**으로 나가는 링크.
 *
 * noopener를 반드시 붙인다 — 없으면 열린 페이지가 window.opener로 이쪽 탭을
 * 다른 주소로 바꿔칠 수 있다(탭내빙). 링크 주소는 관리자가 입력하는 값이라
 * 우리가 통제하지 못한다.
 */
export function openExternal(url: string): void {
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}
