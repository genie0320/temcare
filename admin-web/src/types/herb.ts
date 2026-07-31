import type { ContentStatus } from './weakness'

export interface HerbListItem {
  id: string
  name: string
  hanja: string
  status: ContentStatus
  weakness_names: string[]
  card_count: number
  updated_at: string
}

export interface HerbCardItem {
  id: number
  mechanism: string
  description: string
  weakness_ids: string[]
}

export interface HerbCardDraft {
  mechanism: string
  description: string
  weakness_ids: string[]
}

export interface HerbDetail {
  id: string
  name: string
  hanja: string
  image: string
  status: ContentStatus
  sort: number
  cards: HerbCardItem[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type HerbDraft = Pick<HerbDetail, 'name' | 'hanja' | 'image' | 'status' | 'sort'> & {
  cards: HerbCardDraft[]
}
