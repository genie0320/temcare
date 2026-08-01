import type { ReactNode } from 'react'
import { DetailLayout } from './DetailLayout'
import { MetaPanel } from './MetaPanel'
import { PageHead } from './PageHead'
import { PublishBox } from './PublishBox'

/** 상세 화면 공통 껍데기. docs/05_screen_conventions.md §B — 좌 3/4 본문 + 우 1/4 사이드패널.
 *
 * 사이드패널(게시 박스 + 정보 카드)과 오류 노트는 10개 화면이 전부 같았다. 여기로 모은다.
 * 화면마다 다른 것은 `children`(본문 카드)뿐이다.
 */
export function CrudDetailPage(props: {
  /** useCrudDetail()이 돌려준 것을 그대로 넘긴다. */
  crud: {
    isNew: boolean
    data?: { id: string; created_at?: string; updated_at?: string; updated_by?: string } | undefined
    draft: { status: string } & Record<string, unknown>
    set: (key: never, value: never) => void
    saving: boolean
    errorMsg: string | null
    save: () => void
    remove: () => void
  }
  title: string
  backTo: string
  children: ReactNode
  /** 사이드패널에 덧붙일 것(사용처 역참조 등). */
  extraSide?: ReactNode
}) {
  const { crud, title, backTo, children, extraSide } = props
  const data = crud.data

  return (
    <>
      <PageHead title={title} backTo={backTo} />
      <DetailLayout
        main={
          <>
            {children}
            {crud.errorMsg && (
              <div className="note warn">
                <span className="i">⚠</span> {crud.errorMsg}
              </div>
            )}
          </>
        }
        side={
          <>
            <PublishBox
              status={crud.draft.status as never}
              onStatusChange={(s) => crud.set('status' as never, s as never)}
              onSave={crud.save}
              onDelete={crud.isNew ? undefined : crud.remove}
              saving={crud.saving}
              isNew={crud.isNew}
            />
            <MetaPanel
              id={data?.id ?? ''}
              createdAt={data?.created_at ?? ''}
              updatedAt={data?.updated_at ?? ''}
              updatedBy={data?.updated_by ?? ''}
            />
            {extraSide}
          </>
        }
      />
    </>
  )
}
