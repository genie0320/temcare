// 감사로그·접속기록 조회(adm_028). 백엔드 apps/audit/serializers.py와 짝이다.

export interface Paged<T> {
  count: number
  page: number
  page_size: number
  results: T[]
}

export interface AuditTableSummary {
  target_table: string
  total: number
  oldest_at: string
  latest_at: string
  /** 액션명 → 건수. 예: { create: 12, update: 40 } */
  actions: Record<string, number>
}

export interface AuditSummary {
  audit_log: {
    total: number
    oldest_at: string | null
    latest_at: string | null
    by_action: { action: string; count: number }[]
    by_table: AuditTableSummary[]
  }
  access_log: {
    total: number
    oldest_at: string | null
    latest_at: string | null
  }
  /** ★ 보관 기간 정책 문구가 아니라 '지금 상태'다. docs/11_audit_viewer.md §7 */
  purge: { implemented: boolean; note: string }
}

export interface AuditLogRow {
  id: number
  created_at: string
  actor_id: string | null
  actor_type: string
  ip: string | null
  action: string
  target_table: string
  target_id: string | null
  /** 목록은 잘라서 온다. 전문은 상세(AuditLogDetail)에서만. */
  before_preview: string | null
  after_preview: string | null
  truncated: boolean
}

export interface AuditLogDetail {
  id: number
  created_at: string
  actor_id: string | null
  actor_type: string
  ip: string | null
  action: string
  target_table: string
  target_id: string | null
  before_json: string | null
  after_json: string | null
}

export interface AccessLogRow {
  id: number
  created_at: string
  actor_id: string
  ip: string | null
  target_user: string | null
  fields: string
  purpose: string
}
