import { screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ResultHomeScreen } from './ResultHomeScreen'
import { mockFetch, renderScreen } from '../../../test/render'

// sc_004b 체질분석결과.
//
// ★ 이 화면이 지켜야 하는 것은 **세 가지 상태가 서로 달라 보이는 것**이다.
//     ① 불러오기 실패        → "불러오지 못했어요" + 다시 시도
//     ② 아직 문진을 안 했다  → "아직 문진 결과가 없어요" + 문진 시작하기
//     ③ 이 체질 콘텐츠가 없다 → 개발용 안내
//   예전에는 ①이 ②로 보였다. 결과가 **있는** 회원에게 "문진 시작하기"가 뜬 것이다.
//   서버가 삐끗한 것뿐인데 사용자는 자기 결과가 사라졌다고 읽는다(결정 #33).

const FULL_RESULT = {
  hasResult: true,
  found: true,
  typeId: 'TEM05',
  name: 'TE-5',
  nickname: '매일 겨울을 사는',
  body: { min: 1, max: 3, desc: '마른 편이 많아요.' },
  weaknesses: [{ id: 'WEAK-01', name: '추위', catchphrase: '매일 겨울을 사는 몸' }],
  healthSigns: [{ id: 'SIGN-01', name: '손발이 차다', note: '', image: '' }],
  illnesses: [],
}

afterEach(() => vi.unstubAllGlobals())

describe('체질분석결과', () => {
  it('불러오기에 실패하면 "결과 없음"이 아니라 실패라고 말한다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ status: 500 })))

    renderScreen(<ResultHomeScreen />)

    await waitFor(() => {
      expect(screen.getByText(/불러오지 못했어요/)).toBeInTheDocument()
    })
    // ★ 이게 뜨면 회귀다. 결과가 있는 사람에게 문진을 다시 시키는 화면이 된다.
    expect(screen.queryByText(/아직 문진 결과가 없어요/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '문진 시작하기' })).not.toBeInTheDocument()
  })

  it('정말로 문진 전이면 문진으로 안내한다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: { hasResult: false } })))

    renderScreen(<ResultHomeScreen />)

    expect(await screen.findByText(/아직 문진 결과가 없어요/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '문진 시작하기' })).toBeInTheDocument()
    expect(screen.queryByText(/불러오지 못했어요/)).not.toBeInTheDocument()
  })

  it('문진은 했는데 그 체질 콘텐츠가 없으면 그렇게 알려준다', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch(() => ({ body: { hasResult: true, found: false, typeId: 'TEM33' } })),
    )

    renderScreen(<ResultHomeScreen />)

    expect(await screen.findByText(/TEM33/)).toBeInTheDocument()
    // 문진을 다시 시키면 안 된다 — 문진은 이미 했고, 없는 건 우리 콘텐츠다.
    expect(screen.queryByRole('button', { name: '문진 시작하기' })).not.toBeInTheDocument()
  })

  it('결과가 있으면 체질과 약점을 보여주고 처방으로 가는 문을 낸다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: FULL_RESULT })))

    renderScreen(<ResultHomeScreen />)

    expect(await screen.findByText(/TEM05 · TE-5/)).toBeInTheDocument()
    expect(screen.getByText('추위')).toBeInTheDocument()
    // 결과(판정)에서 처방(행동)으로 넘어가는 유일한 문이다(결정 #28).
    expect(screen.getByRole('button', { name: /인생처방 보기/ })).toBeInTheDocument()
  })

  it('로그인 이후 화면이므로 홈으로 나갈 문이 있다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: FULL_RESULT })))

    renderScreen(<ResultHomeScreen />)

    // 결정 #34 — 결과·처방·한의원은 제목 + 오른쪽 '홈'으로 통일한다.
    expect(await screen.findByRole('button', { name: '홈' })).toBeInTheDocument()
  })
})
