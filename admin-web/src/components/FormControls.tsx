import { useId, type ReactNode } from 'react'

export function FormRow({ label, required, children }: { label: string; required?: boolean; children: ReactNode }) {
  return (
    <div className="form-row">
      <div className="lbl">
        {label} {required && <span className="req">*</span>}
      </div>
      <div className="fld">{children}</div>
    </div>
  )
}

interface TextFieldProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

// listOptions를 주면 "자유텍스트+기존값 자동완성"(spec에 반복 등장하는 패턴 — 영양소
// 관점, 약재 효능기전, 식품 핵심성분)이 된다. 자유 입력은 그대로 유지하고 후보만 보여준다.
export function TextInput({ value, onChange, placeholder, listOptions }: TextFieldProps & { listOptions?: string[] }) {
  const listId = useId()
  return (
    <>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        list={listOptions ? listId : undefined}
      />
      {listOptions && (
        <datalist id={listId}>
          {listOptions.map((o) => (
            <option key={o} value={o} />
          ))}
        </datalist>
      )}
    </>
  )
}

export function TextArea({ value, onChange, placeholder }: TextFieldProps) {
  return <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
}

export function SegToggle<T extends string>({ value, options, onChange }: { value: T; options: T[]; onChange: (v: T) => void }) {
  return (
    <div className="seg">
      {options.map((opt) => (
        <button key={opt} type="button" className={value === opt ? 'on' : ''} onClick={() => onChange(opt)}>
          {opt}
        </button>
      ))}
    </div>
  )
}
