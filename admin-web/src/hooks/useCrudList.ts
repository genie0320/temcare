import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { apiGet } from '../api/client'
import type { WeaknessListItem } from '../types/weakness'

/** 목록 화면의 필터 상태 + 조회를 한 곳에서 다룬다.
 *
 * 마스터 10개가 모두 "검색어 + 필터 몇 개 → 쿼리스트링 → 목록" 구조라 이 훅으로 모았다.
 * 화면은 '어떤 필터가 있는지'만 선언한다. docs/05_screen_conventions.md §A.
 */
export function useCrudList<T>(config: {
  /** API 경로 조각. 예: 'illnesses' → /content/illnesses/ */
  resource: string
  /** react-query 캐시 키. 목록 무효화(useCrudDetail)와 같은 값을 써야 한다. */
  queryKey: string
  /** 필터 이름 목록. 여기 있는 이름이 그대로 쿼리 파라미터가 된다. */
  filterKeys?: readonly string[]
}) {
  const { resource, queryKey, filterKeys = [] } = config
  const [filters, setFilters] = useState<Record<string, string>>(() =>
    Object.fromEntries(filterKeys.map((k) => [k, ''])),
  )

  const setFilter = (key: string, value: string) =>
    setFilters((prev) => ({ ...prev, [key]: value }))

  const query = useQuery({
    queryKey: [queryKey, filters],
    queryFn: () => {
      const params = new URLSearchParams()
      for (const [key, value] of Object.entries(filters)) {
        if (value) params.set(key, value)
      }
      const qs = params.toString()
      return apiGet<T[]>(`/content/${resource}/${qs ? `?${qs}` : ''}`)
    },
  })

  return {
    rows: query.data ?? [],
    isPending: query.isPending,
    isError: query.isError,
    filters,
    setFilter,
  }
}

/** 약점 필터 드롭다운의 선택지. 8개 목록 화면이 똑같이 쓰던 조회다. */
export function useWeaknessOptions() {
  const { data } = useQuery({
    queryKey: ['weaknesses-all'],
    queryFn: () => apiGet<WeaknessListItem[]>('/content/weaknesses/'),
  })
  return data ?? []
}
