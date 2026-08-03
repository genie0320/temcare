// 약관·동의 조회. 백엔드는 /api/consent/*(apps/consent/views.py). 비로그인 호출 가능.

import { apiGet } from './client'

export interface ConsentItem {
  id: string
  name: string
  required: boolean
  /** true면 화면에서 **반드시 별도 체크박스**로 그린다(개인정보보호법 제23조). */
  isSensitive: boolean
  channel: string
  documentId: string | null
  description: string
  sort: number
}

export interface TermsDetail {
  documentId: string
  documentName: string
  version: string
  body: string
  effectiveAt: string
}

export const fetchConsentItems = () => apiGet<ConsentItem[]>('/consent/items/')

export const fetchTerms = (documentId: string) => apiGet<TermsDetail>(`/consent/terms/${documentId}/`)
