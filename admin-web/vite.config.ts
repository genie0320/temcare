import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// docs/08_tech_stack.md §6: /api를 Django로 넘겨 같은 오리진처럼 개발한다.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    // ★ 포트가 밀리면 조용히 다른 포트로 뜨는데, 그 오리진은 Django의
    // CSRF_TRUSTED_ORIGINS에 없어서 저장할 때만 403이 난다("권한이 없다"로 보인다).
    // 원인을 찾기 어려우므로, 포트가 막혀 있으면 여기서 바로 실패하게 한다.
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 업로드 이미지(§4 파일 스토리지) 미리보기용. 배포에서는 nginx가 직접 서빙한다.
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
