import type { ContentStatus } from './weakness'

export interface PointListItem {
  id: string
  name: string
  hanja: string
  description: string
  status: ContentStatus
  weakness_names: string[]
  updated_at: string
}

export interface PointDetail {
  id: string
  name: string
  hanja: string
  description: string
  location: string
  image: string
  video: string
  status: ContentStatus
  sort: number
  weakness_ids: string[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type PointDraft = Pick<
  PointDetail,
  'name' | 'hanja' | 'description' | 'location' | 'image' | 'video' | 'status' | 'sort' | 'weakness_ids'
>
