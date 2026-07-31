import { useQuery } from '@tanstack/react-query'
import { apiGet } from './api/client'

function App() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiGet<{ status: string }>('/health/'),
  })

  return (
    <div style={{ padding: 24 }}>
      <h1>올라케어 관리자</h1>
      <p>
        백엔드 연결:{' '}
        {isPending ? '확인 중…' : isError ? '실패' : `ok (${data?.status})`}
      </p>
    </div>
  )
}

export default App
