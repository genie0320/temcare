// 고객용 결과 조회. 백엔드는 /api/result/*(apps/content/customer_views.py).
// 관리자 콘텐츠 CRUD(/api/content/*)와 다른 경로다 — 그쪽은 관리자 권한을 요구한다.

import { apiGet } from './client'

export interface ResultTeaser {
  typeId: string
  /** 시드에 해당 체질이 없으면 false. 로컬 개발에서 자주 만난다(tem_type 시드 6개). */
  found: boolean
  name?: string
  nickname?: string
}

export interface WeaknessTag {
  id: string
  name: string
  catchphrase: string
}

export interface HealthSignItem {
  id: string
  name: string
  note: string
  image: string
}

export interface IllnessItem {
  id: string
  name: string
  /** 질환별 독립 발병율. 합계가 100%가 아니다. */
  pct: number
  description: string
  image: string
}

export interface MyResult {
  hasResult: boolean
  found?: boolean
  typeId?: string
  name?: string
  nickname?: string
  /** min·max는 0~4 인덱스다(매우마름~매우비만). 0~100 값이 아니다 — 결정 #19. */
  body?: { min: number; max: number; desc: string }
  weaknesses?: WeaknessTag[]
  healthSigns?: HealthSignItem[]
  illnesses?: IllnessItem[]
}

export const fetchResultTeaser = (raw: number) => apiGet<ResultTeaser>(`/result/teaser/${raw}/`)

export const fetchMyResult = () => apiGet<MyResult>('/result/me/')
