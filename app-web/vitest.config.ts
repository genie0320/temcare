import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// 프론트 테스트 설정. vite.config.ts와 나눠 둔다 — 개발 서버 설정(proxy·strictPort)은
// 테스트와 무관하고, 섞어 두면 한쪽을 고치다 다른 쪽을 깨뜨린다.
//
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    // 전역 주입은 쓰지 않는다 — 테스트 파일이 describe/it/expect/vi를 모두
    // 명시적으로 import한다. 어디서 온 이름인지 흐려지지 않게.
    globals: false,
    setupFiles: ['./src/test/setup.ts'],
    // 화면 테스트만 돌린다. 노드 모듈·빌드 산출물은 보지 않는다.
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
