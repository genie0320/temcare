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
    // Cloudflare Tunnel 시연(docs/08_tech_stack.md §10-0). Vite는 모르는 Host로 들어온
    // 요청을 막는데, 터널 주소는 실행할 때마다 무작위라 개별 등록이 안 된다.
    //
    // ★ 여는 것은 **고객 앱(app-web)뿐이다.** 관리자(admin-web)는 이 목록을 갖지
    //   않으므로 터널로 열 수 없다 — 시연에 필요한 것은 고객 화면이고, 관리자에는
    //   회원 개인정보가 있어서 공개 주소로 나가면 안 된다.
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
