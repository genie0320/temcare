import { useState } from 'react'

import type { HealthSignItem, IllnessItem } from '../../../core/api/result'
import { Button } from '../../components/Button'

// 체질분석결과 화면의 아래쪽 두 섹션 — 건강신호 · 예측질환.
//
// 화면설계서 '체질분석결과(1/2)' #7·#8, '(2/2)' #9·#9a를 그대로 옮긴 것이다.
// 한때 sc_005·sc_006으로 화면을 나눴었는데(명세서 v5의 '요약 카드 → 이동' 구조),
// 설계서는 처음부터 **한 화면 스크롤**이었다. 설계서를 따른다.

// ── 내 몸의 건강신호 ──────────────────────────────────────────────
// 설계서 #7: "부가설명이 있는 경우 아코디언ui가 아래로 슬라이드다운.
//            (한번에 1개씩만 노출됨)"

export function HealthSignSection({ signs }: { signs: HealthSignItem[] }) {
  const [openId, setOpenId] = useState<string | null>(null)

  if (signs.length === 0) {
    return <p className="py-md text-hint text-faint">표시할 건강신호가 없어요.</p>
  }

  return (
    <div className="flex flex-col gap-sm">
      {signs.map((sign) => {
        const isOpen = openId === sign.id
        return (
          <div key={sign.id} className="overflow-hidden rounded-md bg-surface">
            <button
              type="button"
              aria-expanded={isOpen}
              // 열려 있던 것을 닫는 게 아니라 **다른 것으로 갈아끼운다** — 한 번에
              // 하나만 열려 있어야 한다(설계서 #7).
              onClick={() => setOpenId(isOpen ? null : sign.id)}
              className="flex w-full items-center gap-md p-md text-left"
            >
              <span className="flex-1 text-body font-bold">{sign.name}</span>
              <span className="text-hint text-gray-300">{isOpen ? '−' : '+'}</span>
            </button>
            {isOpen ? (
              <div className="flex flex-col gap-sm border-t border-border p-md">
                {sign.image ? (
                  <img src={sign.image} alt="" className="w-full rounded-sm object-cover" />
                ) : null}
                <p className="text-hint leading-relaxed text-muted">
                  {sign.note || '설명이 아직 등록되지 않았어요.'}
                </p>
              </div>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}

// ── 주의해야 할 질환 ──────────────────────────────────────────────
// 설계서 #8: "관리자에서 입력한 100% 만점의 그래프가 파이그래프로 노출됨"
// 명세서 sc_006-2: "발병율 차트 · 파이/도넛 · 질환별 % 시각화. 합계 100% 아님"
//
// ★ 이 둘을 같이 만족시키려면 **100을 분모로 고정**해야 한다. 합계로 나누면
//   (30·30·30·10처럼 합이 100인 경우엔 같아 보여도) 합이 60인 체질에서 30%가
//   원의 절반을 차지해 실제보다 크게 읽힌다. 남는 만큼은 회색으로 비워 둔다.

const DONUT_COLORS = ['#2f8f6b', '#3a6ea5', '#e08a3c', '#7a6cc4', '#d15b52', '#256b52']
const RADIUS = 54
const CIRCUM = 2 * Math.PI * RADIUS

function Donut({ illnesses }: { illnesses: IllnessItem[] }) {
  const total = illnesses.reduce((sum, i) => sum + i.pct, 0)
  // 합이 100을 넘는 데이터가 들어오면 원을 한 바퀴 넘겨 겹쳐 그리게 되므로 분모를
  // 키운다. 검증으로 막지 않는 값이라(질환별 독립 수치) 화면이 견뎌야 한다.
  const denominator = Math.max(100, total)

  let offset = 0
  return (
    <svg viewBox="0 0 140 140" className="h-[140px] w-[140px] shrink-0" role="img" aria-label="예측질환 발병율">
      <circle cx="70" cy="70" r={RADIUS} fill="none" stroke="#e0e5e9" strokeWidth="18" />
      {illnesses.map((illness, index) => {
        const length = (illness.pct / denominator) * CIRCUM
        const dash = `${length} ${CIRCUM - length}`
        const el = (
          <circle
            key={illness.id}
            cx="70"
            cy="70"
            r={RADIUS}
            fill="none"
            stroke={DONUT_COLORS[index % DONUT_COLORS.length]}
            strokeWidth="18"
            strokeDasharray={dash}
            strokeDashoffset={-offset}
            transform="rotate(-90 70 70)"
          />
        )
        offset += length
        return el
      })}
      <text x="70" y="66" textAnchor="middle" className="fill-muted" fontSize="11">
        합계
      </text>
      <text x="70" y="84" textAnchor="middle" className="fill-text" fontSize="20" fontWeight="800">
        {total}%
      </text>
    </svg>
  )
}

export function IllnessSection({ illnesses }: { illnesses: IllnessItem[] }) {
  const [selected, setSelected] = useState<IllnessItem | null>(null)

  if (illnesses.length === 0) {
    return <p className="py-md text-hint text-faint">표시할 질환이 없어요.</p>
  }

  return (
    <div className="flex flex-col gap-md">
      <div className="flex items-center gap-md rounded-md bg-surface p-md">
        <Donut illnesses={illnesses} />
        <div className="flex flex-1 flex-col gap-xs">
          {illnesses.map((illness, index) => (
            <div key={illness.id} className="flex items-center gap-sm text-hint">
              <span
                className="h-[10px] w-[10px] shrink-0 rounded-pill"
                style={{ backgroundColor: DONUT_COLORS[index % DONUT_COLORS.length] }}
              />
              <span className="flex-1 truncate">{illness.name}</span>
              <span className="font-bold">{illness.pct}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* 질환 카드(설계서 #9) — 일러스트 + 질환명, 탭 시 상세 모달. */}
      {illnesses.map((illness) => (
        <button
          key={illness.id}
          type="button"
          onClick={() => setSelected(illness)}
          className="flex items-center gap-md rounded-md bg-surface p-md text-left"
        >
          <span className="flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-md bg-primary-soft text-subtitle">
            {illness.image ? (
              <img src={illness.image} alt="" className="h-full w-full rounded-md object-cover" />
            ) : (
              '🩺'
            )}
          </span>
          <span className="flex-1 text-body font-bold">{illness.name}</span>
          <span className="text-subtitle font-extrabold text-primary-dark">{illness.pct}%</span>
          <span className="text-title text-gray-300">›</span>
        </button>
      ))}

      <p className="text-caption leading-relaxed text-faint">
        발병율은 질환별 독립 수치라 모두 더해도 100%가 되지 않을 수 있어요.
      </p>

      {selected ? <IllnessModal illness={selected} onClose={() => setSelected(null)} /> : null}
    </div>
  )
}

// 설계서 #9a 질환 상세 모달 = 명세서 sc_006a.
function IllnessModal({ illness, onClose }: { illness: IllnessItem; onClose: () => void }) {
  return (
    // z-50: Screen의 하단 CTA가 DOM상 뒤에 있어서, z-index가 없으면 모달의 '닫기'
    // 버튼 위에 겹쳐 그려진다(실제로 겹쳤다).
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40" role="dialog" aria-modal>
      <div className="flex max-h-[80vh] w-full max-w-[430px] flex-col gap-md overflow-y-auto rounded-t-xl bg-surface p-lg">
        <div className="flex items-start gap-md">
          <span className="flex h-[56px] w-[56px] shrink-0 items-center justify-center rounded-md bg-primary-soft text-title">
            {illness.image ? (
              <img src={illness.image} alt="" className="h-full w-full rounded-md object-cover" />
            ) : (
              '🩺'
            )}
          </span>
          <div className="flex flex-1 flex-col gap-xs">
            <h2 className="text-subtitle font-extrabold">{illness.name}</h2>
            <span className="text-hint font-bold text-primary-dark">발병율 {illness.pct}%</span>
          </div>
        </div>

        <p className="whitespace-pre-wrap text-body leading-relaxed">
          {illness.description || '상세 설명이 아직 등록되지 않았어요.'}
        </p>

        <p className="text-caption text-faint">본 정보는 참고용이며 진단이 아닙니다.</p>

        <Button variant="ghost" onClick={onClose}>
          확인
        </Button>
      </div>
    </div>
  )
}
