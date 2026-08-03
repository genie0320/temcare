// sc_040 협력 한의원. 백엔드는 /api/partner-clinics/(apps/clinic/customer_views.py).
// 관리자 CRUD(/api/clinics/)와 다른 경로다 — 그쪽은 adm_040 권한을 요구한다.

import { apiGet } from './client'

export interface PartnerClinic {
  id: string
  name: string
  director: string
  /** '경기 안양시'처럼 시/도 + 시/군/구를 이어붙인 값. 서버가 만들어 준다. */
  region: string
  address: string
  phone: string
  hours: string
  intro: string
  image: string
  mapUrl: string
  homepage: string
}

export const fetchPartnerClinics = () =>
  apiGet<{ clinics: PartnerClinic[] }>('/partner-clinics/')
