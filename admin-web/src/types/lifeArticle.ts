import type { ContentStatus } from './weakness'

export type LifeArticleCategory = '체온' | '먹고싸고' | '멘탈' | '체질이야기'

export interface LifeArticleListItem {
  id: string
  category: LifeArticleCategory
  title: string
  image: string
  status: ContentStatus
  updated_at: string
}

export interface LifeArticleDetail {
  id: string
  category: LifeArticleCategory
  title: string
  body: string
  image: string
  video: string
  status: ContentStatus
  sort: number
  nutrient_ids: string[]
  herb_ids: string[]
  food_ids: string[]
  point_ids: string[]
  health_sign_ids: string[]
  illness_ids: string[]
  product_ids: string[]
  article_ids: string[]
  related_article_ids: string[]
  created_at: string
  updated_at: string
  updated_by: string
}

export type LifeArticleDraft = Pick<
  LifeArticleDetail,
  | 'category'
  | 'title'
  | 'body'
  | 'image'
  | 'video'
  | 'status'
  | 'sort'
  | 'nutrient_ids'
  | 'herb_ids'
  | 'food_ids'
  | 'point_ids'
  | 'health_sign_ids'
  | 'illness_ids'
  | 'product_ids'
  | 'article_ids'
  | 'related_article_ids'
>
