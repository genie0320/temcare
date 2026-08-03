import { screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { PrescriptionScreen } from './PrescriptionScreen'
import { mockFetch, renderScreen } from '../../../test/render'

// sc_007 처방 스트림 "내 몸을 아끼는 길" — 이 서비스의 가치가 전부 여기 있다.
//
// 여기서 지키는 것은 둘이다.
//  1. 실패 / 문진 전 / 콘텐츠 없음이 서로 달라 보인다(결정 #33).
//  2. **깔때기의 출구가 사라지지 않는다** — 스트림이 약재에서 끝나고 아무 데도
//     이어지지 않으면 이 서비스의 목적 자체가 없어진다(결정 #8).

const FULL = {
  hasResult: true,
  found: true,
  typeId: 'TEM05',
  name: 'TE-5',
  nickname: '매일 겨울을 사는',
  weaknesses: [{ id: 'WEAK-01', name: '추위', catchphrase: '매일 겨울을 사는 몸' }],
  nutrition: [
    { id: 1, name: '마그네슘', perspective: '순환·이완', description: '설명', image: '' },
  ],
  diet: {
    good: [{ id: 'FOOD-01', component: '고품질단백질', foods: '달걀', description: '', image: '' }],
    limit: [{ id: 'FOOD-02', component: '고나트륨', foods: '라면', description: '', image: '' }],
  },
  life: [
    { id: 'ART-01', kind: '생활', title: '따뜻하게 먹기', body: '', image: '', video: '', weaknesses: ['추위'] },
  ],
  herb: {
    title: '몸의 축을 데우는',
    desc: '설명',
    groups: [
      {
        weaknessId: 'WEAK-01',
        weaknessName: '추위',
        catchphrase: '매일 겨울을 사는 몸',
        items: [{ id: 1, name: '육계', hanja: '肉桂', mechanism: '온열', description: '설명', image: '' }],
      },
    ],
  },
}

afterEach(() => vi.unstubAllGlobals())

describe('처방 스트림', () => {
  it('불러오기에 실패하면 "결과 없음"이 아니라 실패라고 말한다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ status: 500 })))

    renderScreen(<PrescriptionScreen />)

    await waitFor(() => {
      expect(screen.getByText(/불러오지 못했어요/)).toBeInTheDocument()
    })
    expect(screen.queryByText(/아직 문진 결과가 없어요/)).not.toBeInTheDocument()
  })

  it('4정거장을 순서대로 그린다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: FULL })))

    renderScreen(<PrescriptionScreen />)

    expect(await screen.findByText('마그네슘')).toBeInTheDocument()
    expect(screen.getByText('고품질단백질')).toBeInTheDocument()
    expect(screen.getByText('따뜻하게 먹기')).toBeInTheDocument()
    expect(screen.getByText(/육계/)).toBeInTheDocument()
  })

  it('식탁 신호등은 권장과 제한을 모두 보여준다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: FULL })))

    renderScreen(<PrescriptionScreen />)

    // 빨간불이 없으면 신호등으로 읽히지 않는다(결정 #35에서 실제로 걸렸던 문제).
    expect(await screen.findByText(/권장/)).toBeInTheDocument()
    expect(screen.getByText(/제한/)).toBeInTheDocument()
  })

  it('★ 깔때기의 출구(협력 한의원)가 스트림 끝에 반드시 있다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: FULL })))

    renderScreen(<PrescriptionScreen />)

    // 이게 사라지면 처방을 다 읽은 사람이 갈 곳이 없어진다 — 이 서비스의 목적이
    // 판별이 아니라 협력 한의원으로 사람을 보내는 것이기 때문이다(CLAUDE.md §1).
    expect(await screen.findByText(/협력 한의원 정밀 문진/)).toBeInTheDocument()
  })

  it('정거장이 비어도 화면이 무너지지 않는다', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch(() => ({
        body: { ...FULL, nutrition: [], diet: { good: [], limit: [] }, life: [], herb: { title: '', desc: '', groups: [] } },
      })),
    )

    renderScreen(<PrescriptionScreen />)

    // 콘텐츠가 없어도 출구는 남아 있어야 한다.
    expect(await screen.findByText(/협력 한의원 정밀 문진/)).toBeInTheDocument()
  })
})
