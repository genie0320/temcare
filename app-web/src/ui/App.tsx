import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../core/api/client'

function App() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiGet<{ status: string }>('/health/'),
  })

  return (
    <div className="p-6 bg-bg min-h-screen text-text">
      <h1 className="text-xl font-semibold text-primary">올라케어</h1>
      <p className="text-muted mt-2">
        백엔드 연결:{' '}
        {isPending ? '확인 중…' : isError ? '실패' : `ok (${data?.status})`}
      </p>
    </div>
  )
}

export default App
