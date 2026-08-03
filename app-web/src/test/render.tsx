import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { vi } from 'vitest'

// 화면 하나를 테스트에서 그리기 위한 공통 껍데기.
//
// 화면들이 라우터와 react-query에 기대고 있어서, 테스트마다 이 둘을 손으로
// 세우면 설정이 조금씩 갈라진다. 특히 **retry를 끄는 것**이 중요하다 —
// 기본값은 3번 재시도라, 실패 화면을 확인하려는 테스트가 몇 초씩 기다리게 된다.

export function renderScreen(ui: ReactNode, { route = '/' }: { route?: string } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

/** fetch를 통째로 갈아끼운다. `apiGet`이 fetch를 직접 쓰므로 여기가 유일한 경계다. */
export function mockFetch(handler: (url: string) => { status?: number; body?: unknown }) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input.toString()
    const { status = 200, body = {} } = handler(url)
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
    } as Response
  })
}
