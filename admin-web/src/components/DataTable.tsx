import { type ReactNode, useMemo, useState } from 'react'

export interface Column<T> {
  key: string
  label: string
  render: (row: T) => ReactNode
  /** 상태·최종수정처럼 모든 목록에 공통으로 나오는 열은 폭을 고정한다(예: '80px'). */
  width?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  onRowClick?: (row: T) => void
  emptyLabel?: string
  pageSize?: number
}

// docs/05_screen_conventions.md §A: No.열 내림차순 고정 + 행 전체 클릭 + 15/30/50/100 페이징.
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  emptyLabel = '등록된 항목이 없다.',
  pageSize: initialPageSize = 15,
}: DataTableProps<T>) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(initialPageSize)

  const total = rows.length
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const clampedPage = Math.min(page, pageCount)
  const pageRows = useMemo(() => {
    const start = (clampedPage - 1) * pageSize
    return rows.slice(start, start + pageSize)
  }, [rows, clampedPage, pageSize])

  return (
    <>
      <div className="card-body pad0">
        {total === 0 ? (
          <div className="empty">
            <div className="big">🗂️</div>
            {emptyLabel}
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th className="col-no">No.</th>
                {columns.map((col) => (
                  <th key={col.key} style={col.width ? { width: col.width } : undefined}>
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, i) => (
                <tr key={rowKey(row)} className={onRowClick ? 'clickable' : ''} onClick={() => onRowClick?.(row)}>
                  <td className="col-no">{total - ((clampedPage - 1) * pageSize + i)}</td>
                  {columns.map((col) => (
                    <td key={col.key} style={col.width ? { width: col.width } : undefined}>
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {total > 0 && (
        <div className="pager">
          <div className="pager-size">
            쪽당
            <select
              className="selectbox"
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(1)
              }}
            >
              {[15, 30, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n}개
                </option>
              ))}
            </select>
          </div>
          <div className="pager-nav">
            <button disabled={clampedPage <= 1} onClick={() => setPage(clampedPage - 1)}>
              ‹
            </button>
            {Array.from({ length: pageCount }, (_, i) => i + 1).map((n) => (
              <button key={n} className={n === clampedPage ? 'on' : ''} onClick={() => setPage(n)}>
                {n}
              </button>
            ))}
            <button disabled={clampedPage >= pageCount} onClick={() => setPage(clampedPage + 1)}>
              ›
            </button>
          </div>
        </div>
      )}
    </>
  )
}
