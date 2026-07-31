import type { Config } from 'tailwindcss'
import { colors, spacing, radius } from './src/tokens'

// src/tokens.ts가 단일 소스다 — 여기서 값을 새로 정의하지 않고 읽기만 한다.
export default {
  theme: {
    extend: {
      colors: {
        bg: colors.bg,
        surface: colors.surface,
        text: colors.text,
        muted: colors.muted,
        primary: { DEFAULT: colors.primary, dark: colors.primaryDark },
      },
      spacing,
      borderRadius: radius,
    },
  },
} satisfies Config
