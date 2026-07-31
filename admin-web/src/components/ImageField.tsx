import { useRef, useState } from 'react'
import { apiUpload } from '../api/client'

interface ImageFieldProps {
  value: string
  onChange: (value: string) => void
  resource: string
}

const MAX_SIDE = 256

function resizeToBlob(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(reader.error)
    reader.onload = () => {
      const img = new Image()
      img.onerror = () => reject(new Error('이미지를 읽지 못했다'))
      img.onload = () => {
        const scale = Math.min(1, MAX_SIDE / Math.max(img.width, img.height))
        const w = Math.max(1, Math.round(img.width * scale))
        const h = Math.max(1, Math.round(img.height * scale))
        const canvas = document.createElement('canvas')
        canvas.width = w
        canvas.height = h
        canvas.getContext('2d')?.drawImage(img, 0, 0, w, h)
        canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('변환 실패'))), 'image/png')
      }
      img.src = reader.result as string
    }
    reader.readAsDataURL(file)
  })
}

// 대표 이미지 = 파일 선택 → 256px로 축소 → 서버 업로드 → URL을 값으로 저장.
// docs/04_design_system.md §4 — 파일 스토리지 + 경로만 DB(base64 인라인 금지).
export function ImageField({ value, onChange, resource }: ImageFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFile(file: File) {
    setError(null)
    setUploading(true)
    try {
      const blob = await resizeToBlob(file)
      const formData = new FormData()
      formData.append('resource', resource)
      formData.append('file', blob, 'image.png')
      const { url } = await apiUpload<{ url: string }>('/content/image-upload/', formData)
      onChange(url)
    } catch {
      setError('이미지 업로드에 실패했다.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="imgfield">
      <div className="imgthumb">
        {value ? (
          <img src={value} alt="대표 이미지" />
        ) : (
          <span className="muted" style={{ fontSize: 11 }}>
            이미지 없음
          </span>
        )}
      </div>
      <div className="imgfield-actions">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
            e.target.value = ''
          }}
        />
        <button type="button" className="btn sm" disabled={uploading} onClick={() => inputRef.current?.click()}>
          {uploading ? '업로드 중…' : '🖼️ 이미지 선택'}
        </button>
        <button type="button" className="btn sm ghost" disabled={uploading} onClick={() => onChange('')}>
          기본 이미지로
        </button>
        {error && <div className="hint" style={{ color: 'var(--danger)' }}>{error}</div>}
        <div className="hint">정사각형 권장. 넣지 않으면 기본 이미지가 사용된다.</div>
      </div>
    </div>
  )
}
