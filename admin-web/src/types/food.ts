import type { ContentStatus } from './weakness'

export type FoodPolarity = '권장' | '제한'

export interface FoodListItem {
  id: string
  polarity: FoodPolarity
  foods: string
  component: string
  status: ContentStatus
  weakness_names: string[]
  updated_at: string
}

export interface FoodDetail {
  id: string
  polarity: FoodPolarity
  foods: string
  component: string
  description: string
  image: string
  status: ContentStatus
  sort: number
  weakness_ids: string[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type FoodDraft = Pick<
  FoodDetail,
  'polarity' | 'foods' | 'component' | 'description' | 'image' | 'status' | 'sort' | 'weakness_ids'
>
