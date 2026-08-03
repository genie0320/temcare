import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// 테스트마다 화면을 지운다. 안 지우면 앞 테스트가 그린 화면이 남아서
// "찾는 글자가 두 개"라는 엉뚱한 실패가 난다.
afterEach(cleanup)
