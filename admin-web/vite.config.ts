import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// docs/08_tech_stack.md §6: /api를 Django로 넘겨 같은 오리진처럼 개발한다.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
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
