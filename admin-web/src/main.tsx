import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import { ApiError } from './api/client'
import App from './App.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 4xx(권한 없음·없는 자원·잘못된 요청)는 다시 물어도 답이 같다. react-query 기본
      // 재시도(3회 + 지수 백오프)를 그대로 두면 403을 받고도 화면이 7초 넘게
      // '불러오는 중…'에 머물러, **실패가 실패로 보이지 않는다**.
      // CLAUDE.md §5-1 #1과 같은 문제다 — 실패를 실패라고 즉시 말해야 한다.
      // (2026-08-04 adm_028 감사로그 화면에서 pii_read를 빼고 실제로 확인했다.)
      retry: (failureCount, error) => {
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false
        return failureCount < 2
      },
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
