import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// docs/08_tech_stack.md §6: /api를 Django로 넘겨 같은 오리진처럼 개발한다.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // 포트가 밀리면 그 오리진이 Django의 CSRF_TRUSTED_ORIGINS에 없어서 쓰기 요청만
    // 403이 난다 — 원인을 찾기 어려우므로 여기서 바로 실패하게 한다(admin-web과 동일).
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
