import type { ContentStatus } from '../types/weakness'

// docs/05_screen_conventions.md §F: 게시=primary · 검수요청=accent · 초안=faint · 숨김=danger
const DOT_CLASS: Record<ContentStatus, string> = {
  게시: 'st-pub',
  초안: 'st-draft',
  숨김: 'st-hidden',
}

export function StatusBadge({ status }: { status: ContentStatus }) {
  return <span className={`status-dot ${DOT_CLASS[status]}`}>{status}</span>
}
