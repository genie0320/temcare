import type { ContentStatus } from './weakness'

export type ArticleKind = '식이' | '지압·마사지' | '생활' | '뜸'

export interface ArticleListItem {
  id: string
  kind: ArticleKind
  title: string
  status: ContentStatus
  weakness_names: string[]
  updated_at: string
}

export interface ArticleDetail {
  id: string
  kind: ArticleKind
  title: string
  body: string
  image: string
  video: string
  status: ContentStatus
  sort: number
  weakness_ids: string[]
  food_ids: string[]
  point_ids: string[]
  product_ids: string[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type ArticleDraft = Pick<
  ArticleDetail,
  | 'kind'
  | 'title'
  | 'body'
  | 'image'
  | 'video'
  | 'status'
  | 'sort'
  | 'weakness_ids'
  | 'food_ids'
  | 'point_ids'
  | 'product_ids'
>
