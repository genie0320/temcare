import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { apiDelete, apiGet, apiPatch, apiPost } from '../api/client'
import { Card, DetailLayout } from '../components/DetailLayout'
import { FormRow, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { MetaPanel } from '../components/MetaPanel'
import { PageHead } from '../components/PageHead'
import { PublishBox } from '../components/PublishBox'
import type { ProductDetail, ProductDraft } from '../types/product'

const EMPTY_DRAFT: ProductDraft = {
  name: '',
  description: '',
  image: '',
  url: '',
  status: '게시',
  sort: 0,
}

export function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['product', id],
    queryFn: () => apiGet<ProductDetail>(`/content/products/${id}/`),
    enabled: !isNew,
  })

  const [draft, setDraft] = useState<ProductDraft>(EMPTY_DRAFT)
  const [saving, setSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (data) setDraft(data)
  }, [data])

  function set<K extends keyof ProductDraft>(key: K, value: ProductDraft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    if (!draft.name.trim()) {
      setErrorMsg('상품명은 필수다.')
      return
    }
    setErrorMsg(null)
    setSaving(true)
    try {
      const saved = isNew
        ? await apiPost<ProductDetail>('/content/products/', draft)
        : await apiPatch<ProductDetail>(`/content/products/${id}/`, draft)
      await queryClient.invalidateQueries({ queryKey: ['products'] })
      await queryClient.invalidateQueries({ queryKey: ['product'] })
      navigate(`/content/products/${saved.id}`, { replace: true })
    } catch {
      setErrorMsg('저장에 실패했다. 권한을 확인할 것.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm('이 제품을 삭제할까? 요법관리 참고정보 연결도 함께 해제된다.')) return
    await apiDelete(`/content/products/${id}/`)
    await queryClient.invalidateQueries({ queryKey: ['products'] })
    navigate('/content/products')
  }

  return (
    <>
      <PageHead title={isNew ? '제품 상세 · 새 제품' : `제품 상세 · ${data?.name ?? ''}`} backTo="/content/products" />
      <DetailLayout
        main={
          <>
            <Card title="기본정보">
              <div className="form-grid">
                <FormRow label="상품명" required>
                  <TextInput value={draft.name} onChange={(v) => set('name', v)} placeholder="예: 생강 온열팩" />
                </FormRow>
                <FormRow label="상품설명">
                  <TextArea value={draft.description} onChange={(v) => set('description', v)} placeholder="상품 설명" />
                </FormRow>
                <FormRow label="상품 이미지">
                  <ImageField value={draft.image} onChange={(v) => set('image', v)} resource="adm_027" />
                </FormRow>
                <FormRow label="연결 URL">
                  <TextInput value={draft.url} onChange={(v) => set('url', v)} placeholder="https://..." />
                  <div className="hint">상세페이지·구매 링크(선택).</div>
                </FormRow>
              </div>
            </Card>

            {errorMsg && (
              <div className="note warn">
                <span className="i">⚠</span> {errorMsg}
              </div>
            )}
          </>
        }
        side={
          <>
            <PublishBox
              status={draft.status}
              onStatusChange={(s) => set('status', s)}
              onSave={handleSave}
              onDelete={isNew ? undefined : handleDelete}
              saving={saving}
              isNew={isNew}
            />
            <MetaPanel
              id={data?.id ?? ''}
              createdAt={data?.created_at ?? ''}
              updatedAt={data?.updated_at ?? ''}
              updatedBy={data?.updated_by ?? ''}
            />
          </>
        }
      />
    </>
  )
}
