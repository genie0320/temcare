import type { ContentStatus } from './weakness'

export interface ProductListItem {
  id: string
  name: string
  url: string
  status: ContentStatus
  updated_at: string
}

export interface ProductDetail {
  id: string
  name: string
  description: string
  image: string
  url: string
  status: ContentStatus
  sort: number
  created_at: string
  updated_at: string
  updated_by: string
}

export type ProductDraft = Pick<ProductDetail, 'name' | 'description' | 'image' | 'url' | 'status' | 'sort'>
