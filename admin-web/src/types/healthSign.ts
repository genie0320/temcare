import type { ContentStatus } from './weakness'

export interface HealthSignListItem {
  id: string
  name: string
  note: string
  status: ContentStatus
  weakness_names: string[]
  updated_at: string
}

export interface HealthSignDetail {
  id: string
  name: string
  note: string
  image: string
  status: ContentStatus
  sort: number
  weakness_ids: string[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type HealthSignDraft = Pick<
  HealthSignDetail,
  'name' | 'note' | 'image' | 'status' | 'sort' | 'weakness_ids'
>
