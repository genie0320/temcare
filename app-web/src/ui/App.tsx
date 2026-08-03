import { BrowserRouter, Navigate, Route, Routes } from 'react-router'

import { SplashScreen } from './screens/SplashScreen'
import { ConsentScreen } from './screens/onboarding/ConsentScreen'
import { NicknameScreen } from './screens/onboarding/NicknameScreen'
import { PermissionsScreen } from './screens/onboarding/PermissionsScreen'
import { SignupScreen } from './screens/onboarding/SignupScreen'
import { ClinicListScreen } from './screens/clinic/ClinicListScreen'
import { HomeScreen } from './screens/result/HomeScreen'
import { PrescriptionScreen } from './screens/prescription/PrescriptionScreen'
import { ResultHomeScreen } from './screens/result/ResultHomeScreen'
import { ResultTeaserScreen } from './screens/survey/ResultTeaserScreen'
import { SurveyAboutScreen } from './screens/survey/SurveyAboutScreen'
import { SurveyIntroScreen } from './screens/survey/SurveyIntroScreen'
import { SurveyRunScreen } from './screens/survey/SurveyRunScreen'
import { SurveyWaitingScreen } from './screens/survey/SurveyWaitingScreen'
import { RequireAuth } from './RequireAuth'
import { ROUTES } from './routes'

// 흐름은 docs/06_decisions.md #13 — 문진 → 결과 티저(비로그인) → 가입 → 상세 결과.
// 경로와 화면ID 대응은 routes.ts에 있다.

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path={ROUTES.splash} element={<SplashScreen />} />

        {/* 비로그인 구간 */}
        <Route path={ROUTES.surveyIntro} element={<SurveyIntroScreen />} />
        <Route path={ROUTES.surveyAbout} element={<SurveyAboutScreen />} />
        <Route path={ROUTES.survey} element={<SurveyRunScreen />} />
        <Route path={ROUTES.surveyWaiting} element={<SurveyWaitingScreen />} />
        <Route path={ROUTES.resultTeaser} element={<ResultTeaserScreen />} />

        {/* 온보딩 */}
        <Route path={ROUTES.signup} element={<SignupScreen />} />
        <Route path={ROUTES.consent} element={<ConsentScreen />} />

        {/* 가입 이후 — 세션이 없으면 문진 유도로 되돌린다 */}
        <Route element={<RequireAuth />}>
          <Route path={ROUTES.nickname} element={<NicknameScreen />} />
          <Route path={ROUTES.permissions} element={<PermissionsScreen />} />
          <Route path={ROUTES.result} element={<ResultHomeScreen />} />
          {/* 건강신호·예측질환은 결과 화면 안의 섹션이 됐다(결정 #30).
              예전 주소로 들어와도 깨지지 않게 넘겨준다. */}
          <Route path="/result/signs" element={<Navigate to={ROUTES.result} replace />} />
          <Route path="/result/illness" element={<Navigate to={ROUTES.result} replace />} />
          <Route path={ROUTES.prescription} element={<PrescriptionScreen />} />
          <Route path={ROUTES.clinics} element={<ClinicListScreen />} />
          <Route path={ROUTES.home} element={<HomeScreen />} />
        </Route>

        <Route path="*" element={<Navigate to={ROUTES.splash} replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
