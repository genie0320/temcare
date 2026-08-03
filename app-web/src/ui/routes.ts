// 화면 경로 한곳. 명세서 화면ID를 주석으로 병기한다(docs/06_decisions.md #25 —
// 화면ID 표기는 sc_###를 계속 쓴다).
//
// 흐름은 결정 #13을 따른다: 문진 → 결과 티저(비로그인) → 가입 → 상세 결과.

export const ROUTES = {
  splash: '/', // sc_090 스플래시
  surveyIntro: '/survey/intro', // sc_004a 문진 유도
  surveyAbout: '/survey/about', // sc_008 문진 설명 + 생년월일·성별(PPT SURVEY-01)
  survey: '/survey', // sc_009 문진 진행
  surveyWaiting: '/survey/waiting', // sc_009a 결과 대기
  resultTeaser: '/result/teaser', // sc_010 결과 티저(비로그인)

  signup: '/signup', // sc_091 가입·로그인
  consent: '/signup/consent', // sc_092 약관 동의
  nickname: '/signup/nickname', // PPT SIGNUP-02 닉네임 설정
  permissions: '/signup/permissions', // sc_093 접근권한 안내

  // sc_004b 체질분석결과 — 건강신호(sc_005)·예측질환(sc_006)까지 **한 화면**이다.
  // 화면설계서 '체질분석결과 1/2·2/2'가 한 화면의 위·아래이기 때문(결정 #30).
  // 예전에 나눠 뒀던 /result/signs·/result/illness는 이 화면으로 넘긴다.
  result: '/result',
  prescription: '/prescription', // sc_007 처방 스트림 '내 몸을 아끼는 길'
  clinics: '/clinics', // sc_040 협력 한의원 — 깔때기의 출구(결정 #8)
  home: '/home', // sc_101 메인 홈
} as const
