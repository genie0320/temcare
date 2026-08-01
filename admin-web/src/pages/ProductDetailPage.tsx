import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { useCrudDetail } from '../hooks/useCrudDetail'
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
  const crud = useCrudDetail<ProductDraft, ProductDetail>({
    resource: 'products',
    queryKey: 'product',
    listQueryKey: 'products',
    basePath: '/content/products',
    empty: EMPTY_DRAFT,
    required: [{ field: 'name', message: '상품명은 필수다.' }],
    deleteConfirm: '이 제품을 삭제할까? 요법관리 참고정보 연결도 함께 해제된다.',
  })
  const { draft, set, data, isNew } = crud

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '제품 상세 · 새 제품' : `제품 상세 · ${data?.name ?? ''}`}
      backTo="/content/products"
    >
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
    </CrudDetailPage>
  )
}
