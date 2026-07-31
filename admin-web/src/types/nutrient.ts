import type { ContentStatus } from './weakness'

export interface NutrientListItem {
  id: string
  name: string
  status: ContentStatus
  weakness_names: string[]
  card_count: number
  updated_at: string
}

export interface NutrientCardItem {
  id: number
  perspective: string
  description: string
  weakness_ids: string[]
}

export interface NutrientCardDraft {
  perspective: string
  description: string
  weakness_ids: string[]
}

export interface NutrientDetail {
  id: string
  name: string
  image: string
  status: ContentStatus
  sort: number
  cards: NutrientCardItem[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type NutrientDraft = Pick<NutrientDetail, 'name' | 'image' | 'status' | 'sort'> & {
  cards: NutrientCardDraft[]
}
