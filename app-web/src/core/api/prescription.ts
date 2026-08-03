// sc_007 처방 스트림이 쓰는 데이터. 백엔드는 /api/result/prescription/.
//
// 4정거장을 한 번에 받는다 — 한 화면 스크롤이라 정거장마다 왕복하면 스크롤 도중에
// 로딩이 끼어들어 크레센도가 끊긴다(docs/06_decisions.md #2).

import { apiGet } from './client'
import type { WeaknessTag } from './result'

export interface NutritionItem {
  id: number
  name: string
  /** 관점(개선분야). 같은 영양소라도 약점에 따라 설명 각도가 다르다. */
  perspective: string
  description: string
  image: string
}

export interface FoodItem {
  id: string
  /** 핵심성분. 화면에서 굵게 나오는 쪽이다(예: 복합탄수화물). */
  component: string
  /** 실제 식품 목록 문자열(예: 현미·귀리·고구마). */
  foods: string
  description: string
  image: string
}

export interface LifeItem {
  id: string
  /** 식이 · 지압·마사지 · 생활 · 뜸 */
  kind: string
  title: string
  /** 관리자가 쓴 HTML. */
  body: string
  image: string
  video: string
  /** 이 요법이 걸린 약점 중 **내 체질이 가진 것**만. */
  weaknesses: string[]
}

export interface HerbItem {
  id: number
  name: string
  hanja: string
  /** 효능기전. */
  mechanism: string
  description: string
  image: string
}

/** 약점 하나 = 약재 묶음 하나. 캐치프레이즈가 그룹 제목이 된다. */
export interface HerbGroup {
  weaknessId: string | null
  weaknessName: string
  catchphrase: string
  items: HerbItem[]
}

export interface Prescription {
  hasResult: boolean
  found?: boolean
  typeId?: string
  name?: string
  nickname?: string
  weaknesses?: WeaknessTag[]
  nutrition?: NutritionItem[]
  diet?: { good: FoodItem[]; limit: FoodItem[] }
  life?: LifeItem[]
  herb?: { title: string; desc: string; groups: HerbGroup[] }
}

export const fetchPrescription = () => apiGet<Prescription>('/result/prescription/')
