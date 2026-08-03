import { screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ClinicListScreen } from './ClinicListScreen'
import { mockFetch, renderScreen } from '../../../test/render'

// sc_040 협력 한의원 — **깔때기의 출구**다(결정 #8).
//
// ★ 여기가 이 파일이 존재하는 이유다. 예전에는 불러오기에 실패해도
//   "준비된 협력 한의원이 아직 없어요"가 떴다. 서버가 잠깐 삐끗한 것뿐인데
//   사용자에게는 **협력 한의원이 없는 것**으로 읽힌다. 원장이 다른 원장에게
//   시연하는 자리에서 이게 뜨면 그날 시연은 거기서 끝난다(결정 #33).
//
//   이 서비스의 목적이 "협력 한의원으로 사람을 보내는 것"이므로, 이 화면에서
//   거짓 빈 상태가 뜨는 것은 다른 화면보다 몇 배 비싸다.

const CLINIC = {
  id: 'CL-01',
  name: '안양 협력 한의원',
  director: '홍길동',
  region: '경기 안양시',
  address: '',
  phone: '031-000-0000',
  hours: '',
  intro: '',
  image: '',
  mapUrl: '',
  homepage: '',
}

afterEach(() => vi.unstubAllGlobals())

describe('협력 한의원 목록', () => {
  it('불러오기에 실패하면 "없다"고 하지 않고 실패라고 말한다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ status: 500, body: { detail: 'boom' } })))

    renderScreen(<ClinicListScreen />)

    await waitFor(() => {
      expect(screen.getByText(/불러오지 못했어요/)).toBeInTheDocument()
    })
    // ★ 이 문구가 나오면 회귀다. 실패를 빈 목록으로 뭉갠 것이다.
    expect(screen.queryByText(/준비된 협력 한의원이 아직 없어요/)).not.toBeInTheDocument()
  })

  it('실패 화면에는 빠져나갈 문(다시 시도)이 있다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ status: 500 })))

    renderScreen(<ClinicListScreen />)

    // 막다른 길을 만들지 않는다(결정 #33).
    expect(await screen.findByRole('button', { name: '다시 시도' })).toBeInTheDocument()
  })

  it('정말로 목록이 비었을 때만 "아직 없어요"라고 한다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: { clinics: [] } })))

    renderScreen(<ClinicListScreen />)

    expect(await screen.findByText(/준비된 협력 한의원이 아직 없어요/)).toBeInTheDocument()
    expect(screen.queryByText(/불러오지 못했어요/)).not.toBeInTheDocument()
  })

  it('한의원이 있으면 전환 수단(전화)과 함께 보여준다', async () => {
    vi.stubGlobal('fetch', mockFetch(() => ({ body: { clinics: [CLINIC] } })))

    renderScreen(<ClinicListScreen />)

    expect(await screen.findByText('안양 협력 한의원')).toBeInTheDocument()
    // 1차의 유일한 전환 수단은 전화 한 통이다(명세서 sc_040).
    // 하이픈은 떼고 넘긴다 — 일부 기기에서 tel:에 하이픈이 있으면 걸리지 않는다.
    expect(screen.getByRole('link', { name: /전화 걸기/ })).toHaveAttribute('href', 'tel:0310000000')
  })
})
