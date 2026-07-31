import type { ReactNode } from 'react'

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

export function TextInput({ value, onChange, placeholder }: TextFieldProps) {
  return <input type="text" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
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
