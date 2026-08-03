import { useQuery } from '@tanstack/react-query'

import { fetchPartnerClinics, type PartnerClinic } from '../../../core/api/clinic'
import { openExternal, telHref } from '../../../core/platform/external'
import { Screen } from '../../components/Screen'
import { TopBar } from '../../components/TopBar'

// sc_040 협력 한의원 안내 · 목록 — **깔때기의 출구**(docs/06_decisions.md #8).
//
// 이 서비스의 목적은 판별이 아니라 협력 한의원으로 사람을 보내는 것이다. 앱은 30~40문항
// 약식 문진과 약식 결과까지만 하고, 정확히 알고 싶은 사람을 여기로 보낸다.
// 처방 스트림(sc_007)의 마지막에서 이어진다.
//
// ★ 초기 3곳(안양 1·지방 2)이라 **지도 임베드·검색·거리순 정렬을 만들지 않는다**
//   (명세서 sc_040 비고). 지도는 map_url로 외부 앱에 넘긴다.
// ★ 예약 문의 접수는 2차다. 1차의 전환 수단은 **전화 한 통**이다.

export function ClinicListScreen() {
  const { data, isPending } = useQuery({ queryKey: ['partner-clinics'], queryFn: fetchPartnerClinics })
  const clinics = data?.clinics ?? []

  return (
    <Screen header={<TopBar title="협력 한의원" />}>
      <div className="flex flex-col gap-lg pb-lg">
        {/* UI요소 1 — 전환 안내 카피. 여기가 약식에서 정밀로 넘어가는 이유를 말하는 자리다. */}
        <div className="flex flex-col gap-sm rounded-xl bg-primary-soft p-md">
          <h1 className="text-subtitle font-extrabold leading-snug text-primary-dark">
            이 처방을 정확히 받으려면
            <br />
            130문항 정밀 문진이 필요해요
          </h1>
          <p className="text-hint leading-relaxed text-muted">
            앱의 문진은 약식이라 체질을 가늠하는 데까지예요. 협력 한의원에서 정밀 문진을
            받으시면 내 체질에 딱 맞는 처방을 한의사에게 직접 들으실 수 있어요.
          </p>
        </div>

        {isPending ? (
          <p className="py-xl text-center text-body text-muted">불러오는 중…</p>
        ) : clinics.length === 0 ? (
          <p className="py-xl text-center text-body text-muted">
            준비된 협력 한의원이 아직 없어요.
          </p>
        ) : (
          clinics.map((clinic) => <ClinicCard key={clinic.id} clinic={clinic} />)
        )}
      </div>
    </Screen>
  )
}

function ClinicCard({ clinic }: { clinic: PartnerClinic }) {
  return (
    <section className="flex flex-col gap-sm rounded-xl bg-surface p-md">
      {clinic.image ? (
        <img src={clinic.image} alt="" className="h-[140px] w-full rounded-md object-cover" />
      ) : null}

      <div className="flex flex-col gap-xs">
        <h2 className="text-subtitle font-extrabold">{clinic.name}</h2>
        <p className="text-hint text-muted">
          {[clinic.director, clinic.region].filter(Boolean).join(' · ')}
        </p>
        {clinic.intro ? <p className="text-hint leading-relaxed">{clinic.intro}</p> : null}
      </div>

      <dl className="flex flex-col gap-xs text-hint">
        {clinic.address ? <InfoRow label="주소" value={clinic.address} /> : null}
        {clinic.hours ? <InfoRow label="진료시간" value={clinic.hours} /> : null}
      </dl>

      <div className="flex flex-wrap gap-sm pt-xs">
        {/* UI요소 3 — 전화 걸기. 1차의 유일한 전환 수단이라 가장 강한 버튼이다.
            번호가 없는 곳은 버튼을 아예 그리지 않는다 — 눌러도 아무 일이 없는
            버튼은 "전화가 안 되는 한의원"처럼 읽힌다. */}
        {clinic.phone ? (
          <a
            href={telHref(clinic.phone)}
            className="flex flex-1 items-center justify-center rounded-md bg-primary px-md py-sm text-body font-bold text-white"
          >
            📞 전화 걸기
          </a>
        ) : null}
        {/* UI요소 4 — 지도 열기(외부 앱/웹). 임베드하지 않는다. */}
        {clinic.mapUrl ? (
          <button
            type="button"
            onClick={() => openExternal(clinic.mapUrl)}
            className="flex flex-1 items-center justify-center rounded-md border border-border bg-surface px-md py-sm text-body font-bold"
          >
            🗺️ 지도 보기
          </button>
        ) : null}
        {/* UI요소 5 — 홈페이지(선택) */}
        {clinic.homepage ? (
          <button
            type="button"
            onClick={() => openExternal(clinic.homepage)}
            className="text-hint text-muted underline"
          >
            홈페이지
          </button>
        ) : null}
      </div>
    </section>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-sm">
      <dt className="w-[56px] shrink-0 text-faint">{label}</dt>
      <dd className="flex-1 whitespace-pre-wrap text-muted">{value}</dd>
    </div>
  )
}
