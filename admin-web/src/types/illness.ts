import type { ContentStatus } from './weakness'

export interface IllnessListItem {
  id: string
  name: string
  description: string
  status: ContentStatus
  weakness_names: string[]
  updated_at: string
}

export interface IllnessDetail {
  id: string
  name: string
  description: string
  image: string
  status: ContentStatus
  sort: number
  weakness_ids: string[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type IllnessDraft = Pick<
  IllnessDetail,
  'name' | 'description' | 'image' | 'status' | 'sort' | 'weakness_ids'
>
