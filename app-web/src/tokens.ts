// 디자인 토큰 단일 소스. docs/08_tech_stack.md §7 "RN 전환 대비" 2번.
// 색·간격·타이포·반경을 여기 JS 객체로 두고, tailwind.config.ts가 이걸 읽어
// Tailwind 유틸리티를 생성한다. RN 전환 시 이 파일 값만 그대로 넘어간다.
//
// 값 출처: prototype/prescription_stream_mockup.html의 :root 변수.
// 관리자(docs/04_design_system.md)와 같은 계열을 쓰되, 고객 화면은 스케일 전체
// (gray-50~800, green-50~900)가 필요하다 — 처방 스트림의 "크레센도"가 초록 농도
// 차이로 표현되기 때문이다(docs/06_decisions.md #2).

export const colors = {
  // 회색 스케일
  gray50: '#f5f7f8',
  gray100: '#eceff2',
  gray200: '#e0e5e9',
  gray300: '#cdd4db',
  gray400: '#9aa4ad',
  gray500: '#69747f',
  gray700: '#333d47',
  gray800: '#1f2a33',

  // 초록 스케일 — 아래로 갈수록 진해지는 크레센도의 재료
  green50: '#e7f4ee',
  green100: '#cfe9dd',
  green200: '#a8d8c4',
  green500: '#3aa37a',
  green600: '#2f8f6b',
  green700: '#256b52',
  green900: '#1b3d30',

  // 보조색
  blue50: '#e8f0f8',
  blue500: '#3a6ea5',
  red500: '#d15b52',
  red50: '#fdf3f2',
  orange500: '#e08a3c',
  // 처방 스트림 ③ 생활 정거장의 아이콘 배경. 정거장마다 아이콘 색을 달리해
  // 스크롤 중에도 "지금 어느 정거장인지"가 색으로 읽히게 한다(영양=blue, 생활=violet).
  violet50: '#f0eefb',

  // 역할색 — 화면 코드는 원시 스케일이 아니라 되도록 이쪽을 참조한다
  bg: '#f5f7f8',
  surface: '#ffffff',
  border: '#e0e5e9',
  text: '#1f2a33',
  muted: '#69747f',
  faint: '#9aa4ad',
  primary: '#2f8f6b',
  primaryDark: '#256b52',
  primarySoft: '#e7f4ee',
  danger: '#d15b52',
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
  lg: '16px',
  xl: '18px',
  pill: '999px',
} as const

// docs/04_design_system.md §2 — 최소 12px, 본문 15px.
// 고객 화면은 관리자보다 한 단계 크게 간다(모바일 · 히어로 타이틀 27px).
export const fontSize = {
  caption: '12px',
  hint: '13px',
  body: '15px',
  subtitle: '17px',
  title: '21px',
  hero: '27px',
} as const

export const tokens = { colors, spacing, radius, fontSize } as const
export type Tokens = typeof tokens
