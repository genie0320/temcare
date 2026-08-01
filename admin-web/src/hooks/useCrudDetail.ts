import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from '../api/client'

/** 서버가 돌려준 검증 오류를 사람이 읽을 문장으로 바꾼다.
 *
 * ★ 이게 없으면 서버가 "연결 약점은 최소 1개가 필요하다"라고 정확히 알려줘도 화면에는
 *   "저장에 실패했다. 권한을 확인할 것."만 떠서, 권한 문제로 착각하게 된다.
 *   백엔드가 약점 태그 필수 검증(400)을 하기 시작했으므로 반드시 노출해야 한다.
 */
function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return '권한이 없다. 계정 역할을 확인할 것.'
    const detail = error.detail
    if (detail && typeof detail === 'object') {
      const messages = Object.values(detail as Record<string, unknown>)
        .flatMap((v) => (Array.isArray(v) ? v : [v]))
        .filter((v): v is string => typeof v === 'string')
      if (messages.length) return messages.join(' ')
    }
    if (typeof detail === 'string') return detail
  }
  return '저장에 실패했다. 잠시 후 다시 시도할 것.'
}

/** 상세 화면의 편집 상태·저장·삭제를 한 곳에서 다룬다.
 *
 * 마스터 10개가 같은 뼈대(불러오기 → draft 편집 → 저장/삭제)를 복사해 쓰고 있었다.
 * 그 과정에서 화면마다 조금씩 어긋난 것들(삭제 오류 미처리, 서버 메시지 무시,
 * '필수' 별표만 있고 검사 없음)을 여기서 한 번에 바로잡는다.
 */
export function useCrudDetail<Draft extends Record<string, unknown>, Detail extends { id: string }>(config: {
  /** API 경로 조각. 예: 'illnesses' */
  resource: string
  /** 상세 캐시 키 / 목록 캐시 키 */
  queryKey: string
  listQueryKey: string
  /** 화면 경로. 예: '/content/illnesses' */
  basePath: string
  empty: Draft
  /** 비어 있으면 저장을 막을 필드와 그때 보여줄 문구. '필수' 별표와 짝을 맞춘다. */
  required?: { field: keyof Draft; message: string }[]
  /** 삭제 확인 문구. 무엇이 함께 풀리는지 알려준다. */
  deleteConfirm: string
  /** 저장 후 추가로 무효화할 캐시 키(자동완성 목록 등). */
  alsoInvalidate?: string[]
}) {
  const { resource, queryKey, listQueryKey, basePath, empty, required = [], deleteConfirm, alsoInvalidate = [] } = config

  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isPending } = useQuery({
    queryKey: [queryKey, id],
    queryFn: () => apiGet<Detail>(`/content/${resource}/${id}/`),
    enabled: !isNew,
  })

  const [draft, setDraft] = useState<Draft>(empty)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // ★ 편집 중 백그라운드 refetch가 draft를 덮어써 입력이 사라지던 문제를 막는다.
  //   서버에서 새로 받은 값은 '이 레코드를 처음 불러왔을 때' 한 번만 draft에 넣는다.
  const loadedIdRef = useRef<string | null>(null)
  useEffect(() => {
    if (data && loadedIdRef.current !== data.id) {
      loadedIdRef.current = data.id
      setDraft(data as unknown as Draft)
    }
  }, [data])

  // 목록 → '새로 만들기'로 이동했을 때 이전 화면의 draft가 남지 않게 초기화한다.
  useEffect(() => {
    if (isNew) {
      loadedIdRef.current = null
      setDraft(empty)
    }
    // empty는 모듈 상수라 매 렌더 동일하다. id 변화만 신호로 쓴다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, isNew])

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function invalidate() {
    await queryClient.invalidateQueries({ queryKey: [listQueryKey] })
    await queryClient.invalidateQueries({ queryKey: [queryKey] })
    for (const key of alsoInvalidate) {
      await queryClient.invalidateQueries({ queryKey: [key] })
    }
  }

  /** 선언한 필수 항목을 저장 전에 검사한다. 화면마다 제각각이던 것을 규격화. */
  function validate(): string | null {
    for (const rule of required) {
      const value = draft[rule.field]
      const empty =
        value == null ||
        (typeof value === 'string' && !value.trim()) ||
        (Array.isArray(value) && value.length === 0)
      if (empty) return rule.message
    }
    return null
  }

  async function save() {
    const invalid = validate()
    if (invalid) {
      setErrorMsg(invalid)
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<Detail>(`/content/${resource}/`, draft)
        : await apiPatch<Detail>(`/content/${resource}/${id}/`, draft)
      await invalidate()
      navigate(`${basePath}/${saved.id}`, { replace: true })
    } catch (error) {
      setErrorMsg(describeError(error))
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    if (!window.confirm(deleteConfirm)) return
    setErrorMsg(null)
    setSaving(true)
    try {
      // ★ 예전에는 여기에 try/catch가 없어서, 권한이 없으면(403) 아무 반응 없이
      //   죽은 버튼처럼 보였다. 10개 화면 전부 같은 문제였다.
      await apiDelete(`/content/${resource}/${id}/`)
      await invalidate()
      navigate(basePath)
    } catch (error) {
      setErrorMsg(describeError(error))
    } finally {
      setSaving(false)
    }
  }

  return { id, isNew, data, isPending, draft, setDraft, set, saving, errorMsg, save, remove }
}
