// 디자인 토큰 단일 소스. docs/08_tech_stack.md §7 "RN 전환 대비".
// 색·간격·타이포·반경을 여기 JS 객체로 두고, tailwind.config.ts가 이걸 읽어
// Tailwind 유틸리티를 생성한다. RN 전환 시 이 파일 값만 그대로 넘어간다.
//
// ★ 지금은 배관(체크포인트 1)만 증명하는 최소 시작값이다. 실제 값은 M3(처방 스트림)
// 화면을 만들 때 prototype/prescription_stream_mockup.html에서 정식으로 추출한다
// (docs/06_decisions.md #2 크레센도 컨셉 참고).

export const colors = {
  bg: '#fafafa',
  surface: '#ffffff',
  text: '#1f2a33',
  muted: '#69747f',
  primary: '#2f8f6b',
  primaryDark: '#256b52',
} as const

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
} as const

export const radius = {
  sm: '7px',
  md: '10px',
} as const

export const tokens = { colors, spacing, radius } as const
export type Tokens = typeof tokens
