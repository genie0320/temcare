export type WeaknessType = '약점' | 'IDEA'
export type ContentStatus = '게시' | '초안' | '숨김'

export interface WeaknessListItem {
  id: string
  name: string
  wtype: WeaknessType
  catchphrase: string
  status: ContentStatus
  linked_content_count: number
  updated_at: string
}

export interface WeaknessDetail {
  id: string
  name: string
  wtype: WeaknessType
  catchphrase: string
  speaker: string
  source: string
  aphorism: string
  status: ContentStatus
  sort: number
  created_at: string
  updated_at: string
  updated_by: string
}

export type WeaknessDraft = Pick<
  WeaknessDetail,
  'name' | 'wtype' | 'catchphrase' | 'speaker' | 'source' | 'aphorism' | 'status' | 'sort'
>
