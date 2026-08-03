import type { ReactNode } from 'react'

// 입력 폼 부품. sc_008(생년월일·성별)·sc_091(이메일·비밀번호)·SIGNUP-02(닉네임)에서
// 반복되는 형태라 미리 뽑아 두었다.

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-xs">
      <span className="text-hint font-bold text-muted">{label}</span>
      {children}
      {hint ? <span className="text-caption text-faint">{hint}</span> : null}
    </label>
  )
}

interface TextInputProps {
  value: string
  onChange: (value: string) => void
  type?: 'text' | 'email' | 'password' | 'date'
  placeholder?: string
  autoComplete?: string
  maxLength?: number
  /** 오른쪽에 붙는 단위 표기(cm·kg). 설계서 '홈 > TEM문진' #3·#4. */
  unit?: string
  /** 숫자 입력에서 모바일 키패드를 띄운다. type='number'를 쓰지 않는 이유는
   *  스크롤로 값이 바뀌고 브라우저마다 스피너 모양이 달라서다. */
  numeric?: boolean
}

export function TextInput({
  value,
  onChange,
  type = 'text',
  placeholder,
  autoComplete,
  maxLength,
  unit,
  numeric = false,
}: TextInputProps) {
  const input = (
    <input
      type={type}
      inputMode={numeric ? 'numeric' : undefined}
      value={value}
      // 숫자 칸에 글자가 들어가면 서버가 400으로 되돌린다. 애초에 못 넣게 막는다.
      onChange={(e) => onChange(numeric ? e.target.value.replace(/\D/g, '') : e.target.value)}
      placeholder={placeholder}
      autoComplete={autoComplete}
      maxLength={maxLength}
      className="h-[52px] w-full flex-1 rounded-md border border-border bg-surface px-md text-body outline-none focus:border-primary"
    />
  )

  if (!unit) return input
  return (
    <div className="flex items-center gap-sm">
      {input}
      <span className="shrink-0 text-hint text-muted">{unit}</span>
    </div>
  )
}

/** 두세 개 중 하나를 고르는 토글(성별 등). */
export function SegToggle<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly T[]
  value: T | ''
  onChange: (value: T) => void
}) {
  return (
    <div className="flex gap-sm">
      {options.map((option) => (
        <button
          key={option}
          type="button"
          role="radio"
          aria-checked={value === option}
          onClick={() => onChange(option)}
          className={[
            'h-[52px] flex-1 rounded-md border text-body transition-colors',
            value === option
              ? 'border-primary bg-primary-soft font-bold text-primary-dark'
              : 'border-border bg-surface',
          ].join(' ')}
        >
          {option}
        </button>
      ))}
    </div>
  )
}

/** 약관 동의(sc_092)의 체크박스 행. '보기'가 있는 항목은 오른쪽에 링크가 붙는다. */
export function CheckRow({
  checked,
  onToggle,
  label,
  badge,
  onView,
  strong = false,
}: {
  checked: boolean
  onToggle: () => void
  label: string
  badge?: string
  onView?: () => void
  strong?: boolean
}) {
  return (
    <div className="flex items-center gap-sm py-xs">
      <button
        type="button"
        role="checkbox"
        aria-checked={checked}
        onClick={onToggle}
        className="flex flex-1 items-center gap-sm text-left"
      >
        {/* ✓는 체크됐을 때만 그린다. 항상 그려두면 회색 체크가 보여서 '이미 동의함'으로
            읽힌다 — 동의 화면에서 이건 그냥 보기 나쁜 정도가 아니라 위험하다. */}
        <span
          aria-hidden
          className={[
            'flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-pill border text-caption',
            checked ? 'border-primary bg-primary text-white' : 'border-gray-300 bg-surface',
          ].join(' ')}
        >
          {checked ? '✓' : ''}
        </span>
        <span className={strong ? 'text-body font-bold' : 'text-body'}>
          {badge ? <span className="mr-xs text-hint text-primary-dark">{badge}</span> : null}
          {label}
        </span>
      </button>
      {onView ? (
        <button type="button" onClick={onView} className="shrink-0 text-hint text-faint underline">
          보기
        </button>
      ) : null}
    </div>
  )
}
