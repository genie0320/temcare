import type { FormEvent } from 'react'

interface RichTextEditorProps {
  value: string
  onChange: (html: string) => void
}

// 경량 리치에디터. docs/04_design_system.md §2 — 본문 13.5px/line-height 1.75.
// document.execCommand는 구식 API지만 프로토타입과 동일하게 "가볍게"가 목표라 그대로 쓴다.
export function RichTextEditor({ value, onChange }: RichTextEditorProps) {
  function exec(command: string, arg?: string) {
    document.execCommand(command, false, arg)
  }

  function handleInput(e: FormEvent<HTMLDivElement>) {
    onChange(e.currentTarget.innerHTML)
  }

  return (
    <div className="rte">
      <div className="rte-tools">
        <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => exec('bold')}>
          <b>B</b>
        </button>
        <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => exec('italic')}>
          <i>I</i>
        </button>
        <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => exec('formatBlock', 'H4')}>
          제목
        </button>
        <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => exec('insertUnorderedList')}>
          • 목록
        </button>
      </div>
      <div
        className="rte-body"
        contentEditable
        suppressContentEditableWarning
        onInput={handleInput}
        dangerouslySetInnerHTML={{ __html: value }}
      />
    </div>
  )
}
