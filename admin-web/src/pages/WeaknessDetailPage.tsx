import { Card } from '../components/DetailLayout'
import { CrudDetailPage } from '../components/CrudDetailPage'
import { FormRow, TextArea, TextInput, SegToggle } from '../components/FormControls'
import { useCrudDetail } from '../hooks/useCrudDetail'
import type { WeaknessDetail, WeaknessDraft } from '../types/weakness'

const EMPTY_DRAFT: WeaknessDraft = {
  name: '',
  wtype: '약점',
  catchphrase: '',
  speaker: '',
  source: '',
  aphorism: '',
  status: '게시',
  sort: 0,
}

export function WeaknessDetailPage() {
  const crud = useCrudDetail<WeaknessDraft, WeaknessDetail>({
    resource: 'weaknesses',
    queryKey: 'weakness',
    listQueryKey: 'weaknesses',
    basePath: '/content/weaknesses',
    empty: EMPTY_DRAFT,
    required: [
      { field: 'wtype', message: '타입은 필수다.' },
      { field: 'name', message: '약점명은 필수다.' },
    ],
    deleteConfirm: '이 약점을 삭제할까? 콘텐츠에 연결된 태그도 함께 사라진다.',
  })
  const { draft, set, data, isNew } = crud

  return (
    <CrudDetailPage
      crud={crud}
      title={isNew ? '약점 상세 · 새 약점' : `약점 상세 · ${data?.name ?? ''}`}
      backTo="/content/weaknesses"
    >
      <Card title="기본정보">
        <div className="form-grid">
          <FormRow label="타입" required>
            <SegToggle value={draft.wtype} options={['약점', 'IDEA']} onChange={(v) => set('wtype', v)} />
          </FormRow>
          <FormRow label="약점명" required>
            <TextInput value={draft.name} onChange={(v) => set('name', v)} />
          </FormRow>
        </div>
      </Card>
      <Card title="캐치프레이즈" sub="처방화면 그룹 제목용(예: '똥 막힌 하수도')">
        <div className="form-grid">
          <FormRow label="캐치프레이즈">
            <TextInput value={draft.catchphrase} onChange={(v) => set('catchphrase', v)} placeholder="예: 똥 막힌 하수도" />
          </FormRow>
        </div>
      </Card>
      <Card title="격언" sub="각 약점에 노출할 격언">
        <div className="form-grid">
          <FormRow label="화자">
            <TextInput value={draft.speaker} onChange={(v) => set('speaker', v)} />
          </FormRow>
          <FormRow label="출처">
            <TextInput value={draft.source} onChange={(v) => set('source', v)} />
          </FormRow>
          <FormRow label="격언">
            <TextArea value={draft.aphorism} onChange={(v) => set('aphorism', v)} />
          </FormRow>
        </div>
      </Card>
    </CrudDetailPage>
  )
}
