import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { fetchResultTeaser } from '../../../core/api/result'
import { saveDiagnosis } from '../../../core/api/diagnosis'
import { useAuthStore } from '../../../core/store/auth'
import { useSurveyStore } from '../../../core/store/survey'
import { Button } from '../../components/Button'
import { Screen } from '../../components/Screen'
import { ROUTES } from '../../routes'

// sc_010 검사결과 1차 안내 = **결과 티저**(결정 #13).
//
// 비로그인 상태로 보는 화면이고, 유형명·별명까지만 보여준다. '자세히 보기'가
// 가입으로 이어지는 지점이라 여기가 깔때기의 첫 관문이다 — 여기서 다 보여주면
// 가입할 이유가 사라진다.
//
// ★ 단 **이미 로그인한 사람에게는 가입을 다시 묻지 않는다.** 기존 회원이 문진을
//   한 번 더 풀면 여기로 오는데, 그때 가입 화면으로 보내면 서버가 409로 막고
//   화면은 그 자리에서 끝난다 — 결과를 영영 못 보는 막다른 길이었다.

export function ResultTeaserScreen() {
  const navigate = useNavigate()
  const rawValue = useSurveyStore((s) => s.rawValue)
  const clearSurvey = useSurveyStore((s) => s.clear)
  const status = useAuthStore((s) => s.status)
  const bootstrap = useAuthStore((s) => s.bootstrap)
  const [busy, setBusy] = useState(false)

  // 판별 없이 URL로 직접 들어온 경우 문진부터 다시 시킨다.
  //
  // ★ **들어온 순간에만** 판단한다. rawValue를 계속 감시하면, 결과를 저장하고
  //   임시 답안을 비우는 순간(clearSurvey) 이 감시가 "판별값이 없네"로 읽고
  //   문진 처음으로 되돌려 버린다 — 결과 화면으로 가려던 이동을 덮어썼다.
  const hadResultOnEntry = useRef(rawValue !== null)
  useEffect(() => {
    if (!hadResultOnEntry.current) navigate(ROUTES.surveyIntro, { replace: true })
  }, [navigate])

  // 비로그인 화면이지만 세션 유무는 알아야 한다 — 버튼이 갈리기 때문이다.
  useEffect(() => {
    if (status === 'loading') void bootstrap()
  }, [status, bootstrap])

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['result-teaser', rawValue],
    queryFn: () => fetchResultTeaser(rawValue!),
    enabled: rawValue !== null,
  })

  const signedIn = status === 'authenticated'

  async function handleDetail() {
    if (!signedIn) {
      navigate(ROUTES.signup)
      return
    }
    setBusy(true)
    try {
      // 방금 푼 결과를 먼저 저장한다. 이게 없으면 예전 결과가 보인다.
      if (rawValue !== null) await saveDiagnosis(rawValue)
      clearSurvey()
      navigate(ROUTES.result, { replace: true })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Screen
      footer={
        <>
          <Button disabled={busy} onClick={handleDetail}>
            자세히 보기
          </Button>
          <Button variant="text" onClick={() => navigate(ROUTES.surveyIntro)}>
            다시 검사할래요
          </Button>
        </>
      }
    >
      <div className="flex flex-1 flex-col justify-center gap-lg py-xl text-center">
        <p className="text-body text-muted">당신의 체질은</p>

        {isPending ? (
          <p className="text-title text-faint">불러오는 중…</p>
        ) : isError || data === undefined ? (
          // ★ 여기는 카톡 공유로 들어온 사람이 처음 보는 화면이다(결정 #13). 불러오기
          //   실패를 "콘텐츠가 없다"로 뭉뚱그리면, 우리 사정이 아니라 **그 사람의
          //   결과가 없는 것**처럼 읽힌다. 실패는 실패라고 말하고 다시 시도를 준다.
          <div className="flex flex-col items-center gap-sm">
            <p className="text-body text-muted">결과를 불러오지 못했어요.</p>
            <Button variant="ghost" inline onClick={() => void refetch()}>
              다시 시도
            </Button>
          </div>
        ) : data.found ? (
          <div className="flex flex-col items-center gap-sm">
            <span className="rounded-pill bg-primary-soft px-md py-xs text-hint font-bold text-primary-dark">
              {data.typeId}
            </span>
            <h1 className="text-hero font-extrabold leading-tight">{data.name}</h1>
            {data.nickname ? (
              <p className="text-subtitle font-bold text-primary-dark">{data.nickname}</p>
            ) : null}
          </div>
        ) : (
          // 시드에 없는 체질. 개발 중에만 보이는 상태다(📌 tem_type 시드 6개).
          <div className="flex flex-col items-center gap-sm">
            <h1 className="text-title font-extrabold">{data?.typeId}</h1>
            <p className="text-hint text-orange-500">
              아직 이 체질의 콘텐츠가 준비되지 않았어요. (개발용 시드 미완성)
            </p>
          </div>
        )}

        <p className="text-body leading-relaxed text-muted">
          체질에 맞는 <b>영양 · 식이 · 생활 · 약재</b> 처방은
          {signedIn ? (
            <>
              <br />
              바로 이어서 보여드릴게요.
            </>
          ) : (
            <>
              <br />
              가입하시면 바로 보여드릴게요.
            </>
          )}
        </p>
      </div>
    </Screen>
  )
}
