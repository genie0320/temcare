import { useState } from 'react'

import type { FoodItem, HerbGroup, LifeItem, NutritionItem } from '../../../core/api/prescription'

// 처방 스트림의 정거장 본문 4종. 껍데기(노드·카드·스트림 척추)는 PrescriptionScreen이
// 그리고, 여기는 "정거장 안에 무엇이 들어가는가"만 담당한다.
//
// 디자인 기준은 prototype/prescription_stream_mockup.html.

// ── ① 영양 ────────────────────────────────────────────────────────
// 카드 단위 = (영양소 × 관점)이라 같은 영양소가 관점만 달리해 두 번 나올 수 있다.
// 이름이 겹쳐 보여도 버그가 아니다 — key를 이름이 아니라 카드 id로 잡는 이유다.

export function NutritionStation({ items }: { items: NutritionItem[] }) {
  return (
    <div className="flex flex-col">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex gap-sm border-b border-gray-100 py-sm last:border-b-0 last:pb-0"
        >
          <span className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-md bg-blue-50 text-subtitle">
            💊
          </span>
          <div className="flex flex-col gap-[2px]">
            <div className="flex flex-wrap items-center gap-xs">
              <span className="text-body font-bold leading-tight">{item.name}</span>
              {item.perspective ? (
                <span className="rounded-pill bg-blue-50 px-sm text-caption font-bold text-blue-500">
                  {item.perspective}
                </span>
              ) : null}
            </div>
            <p className="text-caption text-muted">{item.description}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── ② 식이 — 식탁 신호등 ──────────────────────────────────────────
// 권장/제한 2블록. 한쪽이 비면 그 블록을 통째로 빼야 한다 — 빈 '제한' 칸이 남으면
// "제한할 게 없다"가 아니라 "데이터가 덜 들어왔다"로 읽힌다.

function SignalRow({
  tone,
  label,
  items,
}: {
  tone: 'good' | 'limit'
  label: string
  items: FoodItem[]
}) {
  const good = tone === 'good'
  return (
    <div className={`flex gap-sm p-sm ${good ? 'bg-green-50' : 'bg-red-50'}`}>
      <span
        className={`w-[62px] shrink-0 text-hint font-extrabold ${good ? 'text-primary' : 'text-danger'}`}
      >
        {label}
      </span>
      <div className="flex flex-col gap-[2px] text-hint">
        {items.map((food) => (
          <p key={food.id}>
            <b className="font-bold">{food.component}</b>{' '}
            <span className="text-muted">{food.foods}</span>
          </p>
        ))}
      </div>
    </div>
  )
}

export function DietStation({ good, limit }: { good: FoodItem[]; limit: FoodItem[] }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-md border border-gray-100">
      {good.length > 0 ? <SignalRow tone="good" label="👍 권장" items={good} /> : null}
      {limit.length > 0 ? <SignalRow tone="limit" label="🚫 제한" items={limit} /> : null}
    </div>
  )
}

// ── ③ 생활 — 요법(식이/지압·마사지/생활/뜸) ───────────────────────
// 명세서 sc_007c는 요법 카드에 **본문**까지 포함한다. 그런데 본문을 다 펼쳐 두면
// 스트림이 한없이 길어져 정거장 ④까지 내려가는 사람이 없다. 그래서 아코디언으로
// 접는다 — 결과화면의 건강신호와 같은 상호작용이라 새로 배울 것도 없다.

const KIND_ICON: Record<string, string> = {
  '식이': '🍵',
  '지압·마사지': '🖐️',
  '생활': '🌙',
  '뜸': '🔥',
}

export function LifeStation({ items }: { items: LifeItem[] }) {
  const [openId, setOpenId] = useState<string | null>(null)

  return (
    <div className="flex flex-col">
      {items.map((item) => {
        const open = openId === item.id
        return (
          <div key={item.id} className="flex flex-col border-t border-gray-100 first:border-t-0">
            <button
              type="button"
              aria-expanded={open}
              onClick={() => setOpenId(open ? null : item.id)}
              className="flex items-center gap-sm py-sm text-left"
            >
              <span className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-md bg-violet-50 text-subtitle">
                {KIND_ICON[item.kind] ?? '🌙'}
              </span>
              <div className="flex flex-1 flex-col gap-[1px]">
                <span className="text-body font-bold leading-tight">{item.title}</span>
                <span className="text-caption text-muted">
                  {[item.kind, ...item.weaknesses].join(' · ')}
                </span>
              </div>
              <span className="shrink-0 text-subtitle text-gray-300">{open ? '⌃' : '›'}</span>
            </button>
            {open ? (
              <div className="flex flex-col gap-sm pb-sm">
                {item.image ? (
                  <img src={item.image} alt="" className="w-full rounded-md object-cover" />
                ) : null}
                {/* 관리자 에디터가 저장한 HTML을 그대로 그린다. 작성자는 운영자뿐이라
                    관리자 CMS와 같은 신뢰 수준이지만, 외부 필자가 생기면 서버 저장
                    시점에 정화(sanitize)가 필요하다 — 📌 docs/07_milestones.md */}
                <div
                  className="text-hint leading-relaxed text-muted"
                  dangerouslySetInnerHTML={{ __html: item.body }}
                />
              </div>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}

// ── ④ 약재 — 스포트라이트 ────────────────────────────────────────
// 어두운 그린 위에 올린다. 다른 정거장과 위계를 확실히 벌리는 것이 크레센도의
// 핵심이다(docs/04_design_system.md §크레센도).
//
// 약점 캐치프레이즈가 그룹 제목이다 — "'똥 막힌 하수도'를 위한 · 변비".
// 이게 있어야 "왜 나한테 이 약재를 주는지"가 카드마다 설명된다.

/** 을/를 조사. '하수도'는 를, '위장'은 을 — 틀리면 그 자리에서 문장이 어색해진다. */
function objectParticle(word: string): string {
  const last = word.trim().at(-1)
  if (!last) return '를'
  const code = last.charCodeAt(0)
  // 한글 음절이 아니면(영문·숫자·기호) 판단할 근거가 없으니 기본값으로 둔다.
  if (code < 0xac00 || code > 0xd7a3) return '를'
  return (code - 0xac00) % 28 === 0 ? '를' : '을'
}

export function HerbSpotlight({
  title,
  desc,
  groups,
}: {
  title: string
  desc: string
  groups: HerbGroup[]
}) {
  const [openId, setOpenId] = useState<number | null>(null)
  const open = groups.flatMap((g) => g.items).find((h) => h.id === openId)

  return (
    <div className="flex flex-col rounded-xl bg-linear-to-br from-green-900 to-green-600 p-md text-white shadow-lg">
      <span className="self-start rounded-pill bg-white/15 px-md py-xs text-caption font-extrabold">
        👑 인생처방 · 체질에 딱 맞는 단 하나
      </span>
      <h2 className="mt-md text-title font-extrabold">약재</h2>
      <p className="mb-md mt-[2px] text-caption text-white/80">
        {desc || '가장 강력하고 확실한 건강법. 나의 약점에 정면으로 답합니다.'}
      </p>
      {title ? <p className="mb-md text-hint font-bold text-white/90">{title}</p> : null}

      {groups.map((group) => (
        <div key={group.weaknessId ?? '기타'} className="flex flex-col">
          {group.catchphrase || group.weaknessName ? (
            <p className="mb-sm mt-sm text-caption font-bold text-white/90">
              ‘{group.catchphrase || group.weaknessName}’
              <span className="font-semibold text-white/60">
                {objectParticle(group.catchphrase || group.weaknessName)} 위한 ·{' '}
                {group.weaknessName}
              </span>
            </p>
          ) : null}
          {group.items.map((herb) => (
            <button
              key={herb.id}
              type="button"
              onClick={() => setOpenId(herb.id)}
              className="mb-sm flex items-center gap-sm rounded-md border border-white/15 bg-white/10 p-sm text-left"
            >
              <span className="flex h-[48px] w-[48px] shrink-0 items-center justify-center rounded-md bg-white/15 text-title">
                🌿
              </span>
              <div className="flex flex-1 flex-col gap-[2px]">
                <span className="text-body font-bold leading-tight">
                  {herb.name}
                  {herb.hanja ? (
                    <small className="ml-xs text-caption font-medium text-white/60">
                      {herb.hanja}
                    </small>
                  ) : null}
                </span>
                <span className="text-caption text-white/80">{herb.description}</span>
              </div>
              <span className="shrink-0 text-subtitle text-white/50">›</span>
            </button>
          ))}
        </div>
      ))}

      {/* 고지문은 접거나 줄이지 않는다. 한약재를 이름과 효능까지 붙여 보여주는
          화면이라 여기서만은 '참고용'으로 부족하다(명세서 sc_007d). */}
      <p className="mt-sm rounded-md bg-black/15 p-sm text-caption leading-relaxed text-white/80">
        ⚠ 위 한약재는 부작용·오남용 방지를 위해 반드시 한의사 진단 후 복용하세요.
      </p>

      {open ? <HerbModal herb={open} onClose={() => setOpenId(null)} /> : null}
    </div>
  )
}

function HerbModal({
  herb,
  onClose,
}: {
  herb: HerbGroup['items'][number]
  onClose: () => void
}) {
  return (
    // z-50: Screen의 footer가 DOM상 뒤에 있어서, z가 없으면 닫기 버튼이 그 아래로 깔린다.
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="flex max-h-[80vh] w-full max-w-[430px] flex-col gap-sm overflow-y-auto rounded-t-xl bg-surface p-lg text-text">
        <h3 className="text-title font-extrabold">
          {herb.name}
          {herb.hanja ? (
            <small className="ml-xs text-hint font-medium text-faint">{herb.hanja}</small>
          ) : null}
        </h3>
        {herb.mechanism ? (
          <span className="self-start rounded-pill bg-primary-soft px-md py-xs text-caption font-bold text-primary-dark">
            {herb.mechanism}
          </span>
        ) : null}
        <p className="text-body leading-relaxed text-muted">{herb.description}</p>
        <p className="text-caption text-faint">
          ⚠ 반드시 한의사 진단 후 복용하세요. 본 정보는 참고용이며 진단이 아닙니다.
        </p>
        <button
          type="button"
          onClick={onClose}
          className="mt-sm rounded-md bg-gray-100 py-md text-body font-bold"
        >
          닫기
        </button>
      </div>
    </div>
  )
}
