import type { Config } from 'tailwindcss'
import { colors, spacing, radius, fontSize } from './src/tokens'

// src/tokens.ts가 단일 소스다 — 여기서 값을 새로 정의하지 않고 읽기만 한다.
export default {
  theme: {
    extend: {
      colors: {
        bg: colors.bg,
        surface: colors.surface,
        border: colors.border,
        text: colors.text,
        muted: colors.muted,
        faint: colors.faint,
        danger: colors.danger,
        primary: {
          DEFAULT: colors.primary,
          dark: colors.primaryDark,
          soft: colors.primarySoft,
        },
        gray: {
          50: colors.gray50,
          100: colors.gray100,
          200: colors.gray200,
          300: colors.gray300,
          400: colors.gray400,
          500: colors.gray500,
          700: colors.gray700,
          800: colors.gray800,
        },
        green: {
          50: colors.green50,
          100: colors.green100,
          200: colors.green200,
          500: colors.green500,
          600: colors.green600,
          700: colors.green700,
          900: colors.green900,
        },
        blue: { 50: colors.blue50, 500: colors.blue500 },
        red: { 50: colors.red50, 500: colors.red500 },
        violet: { 50: colors.violet50 },
        orange: { 500: colors.orange500 },
      },
      spacing,
      borderRadius: radius,
      fontSize: {
        caption: fontSize.caption,
        hint: fontSize.hint,
        body: fontSize.body,
        subtitle: fontSize.subtitle,
        title: fontSize.title,
        hero: fontSize.hero,
      },
    },
  },
} satisfies Config
