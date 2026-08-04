import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import { type ReactNode, useState } from 'react'
import { ApiError, apiGet } from '../api/client'
import { PageHead } from '../components/PageHead'
import type {
  AccessLogRow,
  AuditLogDetail,
  AuditLogRow,
  AuditSummary,
  Paged,
} from '../types/audit'

/** 감사로그·접속기록 조회(adm_028).
 *
 * ★ 이 화면의 목적은 운영이 아니라 **진단**이다 — "지금 어느 테이블에 어떤 로그가
 *   얼마나 남고 있나"를 눈으로 확인하는 것(docs/11_audit_viewer.md §1).
 *   그래서 로그를 예쁘게 가공하지 않는다. before/after는 <pre> + 등폭 글꼴로 원문 그대로.
 *
 * ★ 조회 전용이다. 저장·삭제 버튼이 하나도 없는 것은 실수가 아니라 계약이다 —
 *   audit_log는 append-only이고 쓰기 경로를 만드는 순간 장부가 장부이기를 그만둔다.
 */

type TabKey = 'summary' | 'audit' | 'access'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'summary', label: '요약' },
  { key: 'audit', label: '데이터 변경' },
  { key: 'access', label: '개인정보 열람' },
]

// audit_log.action 원본값 → 한국어 설명. 표에는 **원본값을 그대로** 쓰고 설명은
// 필터 드롭다운에서만 붙인다(원문 확인이 이 화면의 목적이므로).
const ACTION_LABELS: Record<string, string> = {
  create: '생성',
  update: '수정',
  delete: '삭제',
  publish: '게시',
  export: '내보내기',
  deny: '권한 거부',
  read: '접속기록 열람',
}

const PAGE_SIZES = [25, 50, 100, 200]

function fmt(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ko-KR', { hour12: false })
}

function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

/** ★ "불러오기 실패"와 "원래 비어 있음"을 절대 같게 그리지 않는다(CLAUDE.md §5-1 #1).
 *
 * 감사로그가 **비어 보이는 것**은 "로그가 안 쌓이고 있다"는 심각한 신호로 읽힌다.
 * 조회 실패를 빈 목록으로 그리면 그 신호가 가짜로 뜬다. 실패는 실패라고 쓰고
 * 반드시 빠져나갈 문(다시 시도)을 둔다.
 */
function AsyncBlock<T>({
  query,
  children,
}: {
  query: UseQueryResult<T>
  children: (data: T) => ReactNode
}) {
  if (query.isPending) return <div className="empty">불러오는 중…</div>

  if (query.isError) {
    const status = query.error instanceof ApiError ? query.error.status : null
    return (
      <div className="empty">
        <div className="big">⚠️</div>
        {status === 403 ? (
          <>
            이 기록을 볼 권한이 없다.
            <div className="hint" style={{ marginTop: 6 }}>
              개인정보 열람 이력은 <b>pii_read</b> 권한이 따로 필요하다. 콘텐츠 편집
              권한으로는 열리지 않는다(운영자 계정·권한 관리에서 부여).
            </div>
          </>
        ) : status === 404 ? (
          '이 서버에서는 감사로그 조회가 닫혀 있다(공개 데모 모드).'
        ) : (
          <>
            기록을 <b>불러오지 못했다</b>.
            <div className="hint" style={{ marginTop: 6 }}>
              로그가 비어 있는 것이 아니라 조회에 실패한 것이다. 서버 상태를 확인하고
              다시 시도할 것.
            </div>
          </>
        )}
        <div style={{ marginTop: 12 }}>
          <button className="btn" onClick={() => void query.refetch()}>
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  return <>{children(query.data)}</>
}

function ServerPager({
  count,
  page,
  pageSize,
  onPage,
  onPageSize,
}: {
  count: number
  page: number
  pageSize: number
  onPage: (page: number) => void
  onPageSize: (size: number) => void
}) {
  const pageCount = Math.max(1, Math.ceil(count / pageSize))
  return (
    <div className="pager">
      <div className="pager-size">
        {/* 잘라 보낸다는 사실을 숨기지 않는다 — 전체 건수를 항상 같이 쓴다. */}
        전체 {count.toLocaleString('ko-KR')}건 · {page}/{pageCount} 쪽
        <select
          className="selectbox"
          style={{ width: 'auto', marginLeft: 8 }}
          value={pageSize}
          onChange={(e) => {
            onPageSize(Number(e.target.value))
            onPage(1)
          }}
        >
          {PAGE_SIZES.map((n) => (
            <option key={n} value={n}>
              쪽당 {n}개
            </option>
          ))}
        </select>
      </div>
      <div className="pager-nav">
        <button disabled={page <= 1} onClick={() => onPage(page - 1)}>
          ‹
        </button>
        <button disabled={page >= pageCount} onClick={() => onPage(page + 1)}>
          ›
        </button>
      </div>
    </div>
  )
}

function useSummary() {
  return useQuery({
    queryKey: ['audit-summary'],
    queryFn: () => apiGet<AuditSummary>('/audit/summary/'),
  })
}

// ── 탭 1. 요약 — 사용자가 실제로 보고 싶은 것 ────────────────────

function StatBox({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="statbox">
      <div className="k">{label}</div>
      <div className="v">{value}</div>
      {sub && <div className="s">{sub}</div>}
    </div>
  )
}

function SummaryTab() {
  const query = useSummary()

  return (
    <AsyncBlock query={query}>
      {(data) => (
        <>
          {/* ★ "2년 보관" 같은 정책 문구를 쓰지 않는다. 지금 로그를 파기하는 코드가
              어디에도 없어서, 그렇게 쓰면 지키지 않는 약속을 화면에 박아두는 것이 된다.
              docs/11_audit_viewer.md §7 */}
          {!data.purge.implemented && (
            <div className="note warn">
              <span className="i">!</span>
              <span>{data.purge.note}</span>
            </div>
          )}

          <div className="card">
            <div className="card-head">
              <h2>데이터 변경 이력</h2>
              <span className="sub">audit_log</span>
            </div>
            <div className="card-body">
              <div className="statgrid">
                <StatBox label="총 건수" value={data.audit_log.total.toLocaleString('ko-KR')} />
                <StatBox label="가장 오래된 기록" value={fmt(data.audit_log.oldest_at)} />
                <StatBox label="가장 최근 기록" value={fmt(data.audit_log.latest_at)} />
              </div>
              <div className="chips" style={{ marginTop: 14 }}>
                {data.audit_log.by_action.length === 0 ? (
                  <span className="muted">기록 없음</span>
                ) : (
                  data.audit_log.by_action.map((row) => (
                    <span key={row.action} className="chip gray">
                      {row.action} {row.count.toLocaleString('ko-KR')}
                    </span>
                  ))
                )}
              </div>
            </div>
            <div className="card-body pad0">
              {data.audit_log.by_table.length === 0 ? (
                <div className="empty">
                  <div className="big">🗂️</div>
                  아직 남은 변경 이력이 없다.
                </div>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>대상 테이블</th>
                      <th style={{ width: '80px' }}>건수</th>
                      <th>행위별</th>
                      <th style={{ width: '170px' }}>가장 오래된</th>
                      <th style={{ width: '170px' }}>가장 최근</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.audit_log.by_table.map((row) => (
                      <tr key={row.target_table}>
                        <td>
                          <span className="name">{row.target_table}</span>
                        </td>
                        <td>{row.total.toLocaleString('ko-KR')}</td>
                        <td>
                          <div className="chips">
                            {Object.entries(row.actions).map(([action, count]) => (
                              <span key={action} className="chip gray">
                                {action} {count}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td>
                          <span className="muted">{fmt(row.oldest_at)}</span>
                        </td>
                        <td>
                          <span className="muted">{fmt(row.latest_at)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <h2>개인정보 열람 이력</h2>
              <span className="sub">access_log</span>
            </div>
            <div className="card-body">
              <div className="statgrid">
                <StatBox label="총 건수" value={data.access_log.total.toLocaleString('ko-KR')} />
                <StatBox label="가장 오래된 기록" value={fmt(data.access_log.oldest_at)} />
                <StatBox label="가장 최근 기록" value={fmt(data.access_log.latest_at)} />
              </div>
              {data.access_log.total === 0 && (
                <div className="hint" style={{ marginTop: 10 }}>
                  0건이다. 회원 개인정보를 여는 화면(회원 관리·1:1 문의)이 아직 없어서
                  기록될 일이 없었다 — 그 화면들이 붙을 때 열람 기록이 남기 시작한다.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </AsyncBlock>
  )
}

// ── 탭 2. 데이터 변경(audit_log) ─────────────────────────────────

function LogDump({ title, raw }: { title: string; raw: string | null }) {
  return (
    <div>
      <h4>{title}</h4>
      <pre className="logdump">{raw ?? '(없음)'}</pre>
    </div>
  )
}

function AuditLogDetailCard({ id, onClose }: { id: number; onClose: () => void }) {
  const query = useQuery({
    queryKey: ['audit-log', id],
    queryFn: () => apiGet<AuditLogDetail>(`/audit/logs/${id}/`),
  })

  return (
    <div className="card">
      <div className="card-head">
        <h2>변경 상세</h2>
        <span className="sub">#{id} · 원문 그대로</span>
        <div className="r">
          <button className="btn ghost sm" onClick={onClose}>
            닫기
          </button>
        </div>
      </div>
      <div className="card-body">
        <AsyncBlock query={query}>
          {(log) => (
            <>
              <div className="statgrid" style={{ marginBottom: 14 }}>
                <StatBox label="일시" value={fmt(log.created_at)} />
                <StatBox
                  label="계정"
                  value={log.actor_id ?? '—'}
                  sub={`${log.actor_type} · ${log.ip ?? 'IP 없음'}`}
                />
                <StatBox
                  label="대상"
                  value={log.target_table}
                  sub={`${log.action} · ${log.target_id ?? '—'}`}
                />
              </div>
              <div className="logdiff">
                <LogDump title="변경 전 (before_json)" raw={log.before_json} />
                <LogDump title="변경 후 (after_json)" raw={log.after_json} />
              </div>
            </>
          )}
        </AsyncBlock>
      </div>
    </div>
  )
}

function AuditLogTab() {
  const summary = useSummary()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    actor: '',
    action: '',
    target_table: '',
  })
  const [selected, setSelected] = useState<number | null>(null)

  const setFilter = (key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }

  const query = useQuery({
    queryKey: ['audit-logs', filters, page, pageSize],
    queryFn: () =>
      apiGet<Paged<AuditLogRow>>(`/audit/logs/${qs({ ...filters, page, page_size: pageSize })}`),
  })

  const actions = summary.data?.audit_log.by_action.map((row) => row.action) ?? []
  const tables = summary.data?.audit_log.by_table.map((row) => row.target_table) ?? []

  return (
    <>
      <div className="card">
        <div className="toolbar logfilter">
          <span className="lab">기간</span>
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) => setFilter('date_from', e.target.value)}
          />
          <span className="lab">~</span>
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) => setFilter('date_to', e.target.value)}
          />
          <input
            type="text"
            placeholder="행위자 계정 id"
            value={filters.actor}
            onChange={(e) => setFilter('actor', e.target.value)}
          />
          <select
            className="selectbox"
            value={filters.action}
            onChange={(e) => setFilter('action', e.target.value)}
          >
            <option value="">행위 전체</option>
            {actions.map((action) => (
              <option key={action} value={action}>
                {action}
                {ACTION_LABELS[action] ? ` · ${ACTION_LABELS[action]}` : ''}
              </option>
            ))}
          </select>
          <select
            className="selectbox"
            value={filters.target_table}
            onChange={(e) => setFilter('target_table', e.target.value)}
          >
            <option value="">대상 테이블 전체</option>
            {tables.map((table) => (
              <option key={table} value={table}>
                {table}
              </option>
            ))}
          </select>
        </div>

        <AsyncBlock query={query}>
          {(data) => (
            <>
              <div className="card-body pad0">
                {data.results.length === 0 ? (
                  <div className="empty">
                    <div className="big">🗂️</div>
                    조건에 맞는 변경 이력이 없다.
                  </div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th style={{ width: '170px' }}>일시</th>
                        <th style={{ width: '110px' }}>계정 · IP</th>
                        <th style={{ width: '80px' }}>행위</th>
                        <th style={{ width: '180px' }}>대상</th>
                        <th>변경 전 · 후 (원문 일부)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.results.map((row) => (
                        <tr
                          key={row.id}
                          className="clickable"
                          onClick={() => setSelected(row.id)}
                        >
                          <td>
                            <span className="muted">{fmt(row.created_at)}</span>
                          </td>
                          <td>
                            <span className="name">{row.actor_id ?? '—'}</span>
                            <div className="muted">{row.ip ?? '—'}</div>
                          </td>
                          <td>
                            <span className="chip gray">{row.action}</span>
                          </td>
                          <td>
                            <span className="name">{row.target_table}</span>
                            <div className="muted">{row.target_id ?? '—'}</div>
                          </td>
                          <td>
                            <pre className="logdump inline">
                              {row.before_preview ?? '(없음)'} → {row.after_preview ?? '(없음)'}
                            </pre>
                            {row.truncated && (
                              <div className="hint">잘렸다 — 행을 눌러 전문을 볼 것</div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
              <ServerPager
                count={data.count}
                page={data.page}
                pageSize={data.page_size}
                onPage={setPage}
                onPageSize={setPageSize}
              />
            </>
          )}
        </AsyncBlock>
      </div>

      {selected !== null && (
        <AuditLogDetailCard id={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}

// ── 탭 3. 개인정보 열람(access_log) ──────────────────────────────

function AccessLogTab() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    actor: '',
    target_user: '',
  })

  const setFilter = (key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }

  const query = useQuery({
    queryKey: ['access-logs', filters, page, pageSize],
    queryFn: () =>
      apiGet<Paged<AccessLogRow>>(
        `/audit/access-logs/${qs({ ...filters, page, page_size: pageSize })}`,
      ),
  })

  return (
    <div className="card">
      <div className="toolbar logfilter">
        <span className="lab">기간</span>
        <input
          type="date"
          value={filters.date_from}
          onChange={(e) => setFilter('date_from', e.target.value)}
        />
        <span className="lab">~</span>
        <input
          type="date"
          value={filters.date_to}
          onChange={(e) => setFilter('date_to', e.target.value)}
        />
        <input
          type="text"
          placeholder="열람자 계정 id"
          value={filters.actor}
          onChange={(e) => setFilter('actor', e.target.value)}
        />
        <input
          type="text"
          placeholder="대상 회원 id"
          value={filters.target_user}
          onChange={(e) => setFilter('target_user', e.target.value)}
        />
      </div>

      <AsyncBlock query={query}>
        {(data) => (
          <>
            <div className="card-body pad0">
              {data.results.length === 0 ? (
                <div className="empty">
                  <div className="big">🗂️</div>
                  조건에 맞는 개인정보 열람 이력이 없다.
                </div>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th style={{ width: '170px' }}>일시</th>
                      <th style={{ width: '110px' }}>열람자 · IP</th>
                      <th style={{ width: '110px' }}>대상 회원</th>
                      <th style={{ width: '160px' }}>열람 항목</th>
                      <th>열람 사유</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.results.map((row) => (
                      <tr key={row.id}>
                        <td>
                          <span className="muted">{fmt(row.created_at)}</span>
                        </td>
                        <td>
                          <span className="name">{row.actor_id}</span>
                          <div className="muted">{row.ip ?? '—'}</div>
                        </td>
                        <td>
                          <span className="name">{row.target_user ?? '—'}</span>
                        </td>
                        <td>
                          <span className="muted">{row.fields || '—'}</span>
                        </td>
                        <td>
                          <pre className="logdump">{row.purpose}</pre>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <ServerPager
              count={data.count}
              page={data.page}
              pageSize={data.page_size}
              onPage={setPage}
              onPageSize={setPageSize}
            />
          </>
        )}
      </AsyncBlock>
    </div>
  )
}

export function AuditLogPage() {
  const [tab, setTab] = useState<TabKey>('summary')

  return (
    <>
      <PageHead
        title="감사로그 · 접속기록"
        description="누가 무엇을 바꿨고 누가 개인정보를 열었는지 원문 그대로 확인한다. 조회 전용이며 수정·삭제 경로가 없다."
      />
      <div className="tabs-bar">
        <div className="seg">
          {TABS.map((item) => (
            <button
              key={item.key}
              className={tab === item.key ? 'on' : ''}
              onClick={() => setTab(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'summary' && <SummaryTab />}
      {tab === 'audit' && <AuditLogTab />}
      {tab === 'access' && <AccessLogTab />}
    </>
  )
}
