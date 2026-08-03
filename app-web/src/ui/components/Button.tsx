import type { ReactNode } from 'react'

// 고객 화면의 버튼. 화면설계서의 하단 CTA가 전부 이 모양이다(폭 꽉 채움 + 둥근 모서리).

type Variant = 'primary' | 'ghost' | 'text'

interface ButtonProps {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: Variant
  type?: 'button' | 'submit'
  /** 폼 안에서 쓸 때 등, 폭을 내용에 맞추고 싶을 때. */
  inline?: boolean
}

const VARIANT_CLASS: Record<Variant, string> = {
  primary: 'bg-primary text-white',
  ghost: 'bg-surface text-text border border-border',
  text: 'bg-transparent text-muted underline',
}

export function Button({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  type = 'button',
  inline = false,
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={[
        'flex items-center justify-center rounded-md px-lg text-body font-bold transition-opacity',
        variant === 'text' ? 'py-sm' : 'h-[52px]',
        inline ? 'self-start' : 'w-full',
        VARIANT_CLASS[variant],
        // 비활성 상태를 확실히 구분한다 — sc_092는 필수 동의 전까지 눌리면 안 된다.
        disabled ? 'cursor-not-allowed opacity-40' : 'cursor-pointer',
      ].join(' ')}
    >
      {children}
    </button>
  )
}
