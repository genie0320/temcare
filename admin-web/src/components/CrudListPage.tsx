import { useNavigate } from 'react-router'
import { DataTable, type Column } from './DataTable'
import { PageHead } from './PageHead'
import { StatusBadge } from './StatusBadge'
import { useCrudList, useWeaknessOptions } from '../hooks/useCrudList'

export type FilterSpec =
  | { kind: 'search'; key: 'search'; placeholder: string }
  | { kind: 'weakness'; key: 'weakness' }
  | { kind: 'select'; key: string; allLabel: string; options: readonly string[] }

/** 목록 화면 공통 껍데기. docs/05_screen_conventions.md §A 규격을 여기 한 곳에만 둔다.
 *
 * 화면은 '무엇이 다른지'(제목·필터·열)만 넘긴다.
 */
export function CrudListPage<T extends { id: string }>(props: {
  title: string
  description: string
  resource: string
  queryKey: string
  newLabel: string
  emptyLabel: string
  filters: FilterSpec[]
  columns: Column<T>[]
}) {
  const { title, description, resource, queryKey, newLabel, emptyLabel, filters, columns } = props
  const navigate = useNavigate()
  const weaknesses = useWeaknessOptions()
  const needsWeakness = filters.some((f) => f.kind === 'weakness')

  const { rows, isPending, isError, filters: values, setFilter } = useCrudList<T>({
    resource,
    queryKey,
    filterKeys: filters.map((f) => f.key),
  })

  return (
    <>
      <PageHead
        title={title}
        description={description}
        actions={
          <button className="btn primary" onClick={() => navigate(`/content/${resource}/new`)}>
            {newLabel}
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          {filters.map((filter) => {
            if (filter.kind === 'search') {
              return (
                <div className="search" key={filter.key}>
                  <input
                    placeholder={filter.placeholder}
                    value={values[filter.key] ?? ''}
                    onChange={(e) => setFilter(filter.key, e.target.value)}
                  />
                </div>
              )
            }
            const options =
              filter.kind === 'weakness'
                ? weaknesses.map((w) => ({ value: w.id, label: w.name }))
                : filter.options.map((o) => ({ value: o, label: o }))
            const allLabel = filter.kind === 'weakness' ? '약점 전체' : filter.allLabel
            return (
              <select
                key={filter.key}
                className="selectbox"
                value={values[filter.key] ?? ''}
                onChange={(e) => setFilter(filter.key, e.target.value)}
                disabled={filter.kind === 'weakness' && needsWeakness && weaknesses.length === 0}
              >
                <option value="">{allLabel}</option>
                {options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            )
          })}
        </div>
        {isPending ? (
          <div className="empty">불러오는 중…</div>
        ) : isError ? (
          <div className="empty">목록을 불러오지 못했다.</div>
        ) : (
          <DataTable
            columns={columns}
            rows={rows}
            rowKey={(row) => row.id}
            onRowClick={(row) => navigate(`/content/${resource}/${row.id}`)}
            emptyLabel={emptyLabel}
          />
        )}
      </div>
    </>
  )
}

// ── 열 공장(column factories) ────────────────────────────────────
// 같은 모양의 열이 8~10개 화면에 복사돼 있던 것을 여기로 모은다.

export const statusFilter = (): FilterSpec => ({
  kind: 'select',
  key: 'status',
  allLabel: '상태 전체',
  options: ['게시', '초안', '숨김'],
})

export const searchFilter = (placeholder: string): FilterSpec => ({
  kind: 'search',
  key: 'search',
  placeholder,
})

export const weaknessFilter = (): FilterSpec => ({ kind: 'weakness', key: 'weakness' })

/** 항목명 + 회색 id. 10개 목록이 모두 같은 모양이다. */
export function nameColumn<T extends { id: string }>(
  label: string,
  pick: (row: T) => string,
): Column<T> {
  return {
    key: 'name',
    label,
    render: (row) => (
      <>
        <span className="name">{pick(row)}</span> <span className="muted">{row.id}</span>
      </>
    ),
  }
}

export function textColumn<T>(key: string, label: string, pick: (row: T) => string): Column<T> {
  return { key, label, render: (row) => <span className="muted">{pick(row) || '—'}</span> }
}

/** 약점 태그 칩. 8개 화면에 동일하게 복사돼 있던 열. */
export function weaknessChipsColumn<T extends { weakness_names: string[] }>(): Column<T> {
  return {
    key: 'weakness_names',
    label: '약점 태그',
    render: (row) =>
      row.weakness_names.length ? (
        <div className="chips">
          {row.weakness_names.map((name) => (
            <span key={name} className="chip">
              {name}
            </span>
          ))}
        </div>
      ) : (
        <span className="muted">—</span>
      ),
  }
}

export function statusColumn<T extends { status: string }>(): Column<T> {
  return {
    key: 'status',
    label: '상태',
    width: '80px',
    render: (row) => <StatusBadge status={row.status as never} />,
  }
}
