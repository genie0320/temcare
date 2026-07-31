import type { ContentStatus } from './weakness'

export interface TemTypeListItem {
  id: string
  name: string
  nickname: string
  status: ContentStatus
  weakness_names: string[]
  updated_at: string
}

export interface IllnessLink {
  illness_id: string
  pct: number
}

export interface TemTypeDetail {
  id: string
  name: string
  nickname: string
  body_min: number
  body_max: number
  body_desc: string
  herb_title: string
  herb_desc: string
  status: ContentStatus
  sort: number
  weakness_ids: string[]
  illnesses: IllnessLink[]
  nutrient_card_ids: string[]
  herb_card_ids: string[]
  food_ids: string[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type TemTypeDraft = Pick<
  TemTypeDetail,
  | 'name'
  | 'nickname'
  | 'body_min'
  | 'body_max'
  | 'body_desc'
  | 'herb_title'
  | 'herb_desc'
  | 'status'
  | 'sort'
  | 'weakness_ids'
  | 'illnesses'
  | 'nutrient_card_ids'
  | 'herb_card_ids'
  | 'food_ids'
>

export interface CandidateItem {
  id: string
  name: string
  sub: string
  polarity?: '권장' | '제한'
}

export interface IllnessOption {
  id: string
  name: string
}
