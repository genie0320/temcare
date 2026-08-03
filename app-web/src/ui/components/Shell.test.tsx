import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Screen } from './Screen'
import { TabBar } from './TabBar'
import { TopBar } from './TopBar'
import { renderScreen } from '../../test/render'

// 화면 껍데기(상단·하단)의 공통 규칙. 결정 #34.
//
// 여기 있는 것들은 **눈에 잘 안 띄는 종류의 회귀**라 테스트로 잠근다. 화면 하나만
// 보면 멀쩡한데 눌러서 넘어가 보면 어긋나는 것들이다.

describe('Screen — 상단 리듬', () => {
  it('상단 바가 없어도 같은 높이를 비운다', () => {
    const { container } = renderScreen(<Screen>본문</Screen>)

    // ★ 이게 없으면 상단 바가 있는 화면과 오갈 때 본문이 52px씩 튄다.
    //   "화면은 다 멀쩡한데 흐름이 매끄럽지 않다"의 실제 원인이었다.
    expect(container.querySelector('.h-\\[52px\\]')).not.toBeNull()
  })

  it('bare를 준 화면(스플래시)만 그 자리를 비우지 않는다', () => {
    const { container } = renderScreen(
      <Screen bare center>
        올라
      </Screen>,
    )

    expect(container.querySelector('.h-\\[52px\\]')).toBeNull()
  })
})

describe('TopBar — 로그인 이후 화면의 공통 규칙', () => {
  it('homeLink를 주면 홈으로 나갈 문이 생긴다', () => {
    renderScreen(<TopBar title="협력 한의원" homeLink />)

    expect(screen.getByText('협력 한의원')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '홈' })).toBeInTheDocument()
  })

  it('hideBack이면 뒤로가기를 그리지 않는다', () => {
    renderScreen(<TopBar title="체질분석결과" hideBack homeLink />)

    expect(screen.queryByRole('button', { name: '뒤로 가기' })).not.toBeInTheDocument()
  })
})

describe('TabBar — 1차는 홈/더보기 2탭', () => {
  it('아직 화면이 없는 탭(더보기)은 눌리지 않는다', () => {
    renderScreen(<TabBar active="home" />)

    // 눌러도 아무 일이 없는 탭은 "고장났나"로 읽힌다. 갈 곳이 생길 때(M5)까지
    // 비활성으로 둔다 — 빈 화면을 만들어 붙이지 않는 이유는 그게 "곧 생긴다"는
    // 신호가 되어 범위를 다시 부풀리기 때문이다(CLAUDE.md §2-3).
    expect(screen.getByRole('button', { name: /더보기/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: /홈/ })).toBeEnabled()
  })

  it('트래커·TEM라이프 탭을 미리 세워두지 않는다', () => {
    renderScreen(<TabBar active="home" />)

    // 보류·이연된 것을 탭으로 세워두면 범위가 다시 부푼다(결정 #10·#11).
    expect(screen.queryByText(/트래커/)).not.toBeInTheDocument()
    expect(screen.queryByText(/TEM라이프/)).not.toBeInTheDocument()
  })
})
