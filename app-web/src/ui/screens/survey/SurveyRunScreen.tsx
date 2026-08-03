import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { fetchQuestionnaire } from '../../../core/survey/provider'
import { isAnswered, type Answer, type Question } from '../../../core/survey/types'
import { useSurveyStore } from '../../../core/store/survey'
import { Button } from '../../components/Button'
import { ChoiceList } from '../../components/ChoiceList'
import { ConfirmSheet } from '../../components/ConfirmSheet'
import { ProgressBar } from '../../components/ProgressBar'
import { Screen } from '../../components/Screen'
import { SliderChoice } from '../../components/SliderChoice'
import { TopBar } from '../../components/TopBar'
import { ROUTES } from '../../routes'

// sc_009 문진 진행 — 문항 카드 + 진행률 + 이전/다음.
//
// 응답은 서버로 가지 않는다. useSurveyStore(클라이언트)에만 쌓였다가 sc_009a에서
// 판별 API에 한 번 넘어가고, diagnosis_result는 가입 이후에야 만들어진다
// (docs/02_architecture_constraints.md §6).
//
// 문항 유형 3종을 여기서 분기한다 — 어떤 유형이 오든 화면은 이 파일 하나다.
//
// ★ 중도 이탈: 30문항짜리 문진에 출구가 없으면 안 된다. 상단 '그만두기'로 한 번에
//   빠져나가되, 되돌리기 어려운 인상을 주지 않도록 "저장된다"는 사실을 확인창에서
//   알린다. 명세서 sc_009에도 화면설계서에도 없던 요소이며 사용자 확인을 받아 넣었다.

/** 아직 답하지 않은 첫 문항. 다 answered면 마지막 문항. 이탈 후 재진입 지점이다. */
function resumeIndexOf(questions: Question[], answers: Answer[]): number {
  const answeredIds = new Set(answers.filter((a) => a.optionIds.length > 0).map((a) => a.questionId))
  const next = questions.findIndex((q) => !answeredIds.has(q.id))
  return next === -1 ? questions.length - 1 : next
}

export function SurveyRunScreen() {
  const navigate = useNavigate()
  // null = 아직 이어풀기 지점을 못 정한 상태(문항이 로딩 중).
  const [index, setIndex] = useState<number | null>(null)
  const [askingExit, setAskingExit] = useState(false)

  const { data: questionnaire, isPending } = useQuery({
    queryKey: ['questionnaire'],
    queryFn: fetchQuestionnaire,
  })
  const answers = useSurveyStore((s) => s.answers)
  const setAnswer = useSurveyStore((s) => s.setAnswer)

  // 문항이 도착하면 딱 한 번, 마지막으로 답한 다음 문항으로 이동한다.
  // 명세서 sc_009의 "이탈 시 임시저장"은 저장만이 아니라 **이어서 풀리는 것**까지다.
  useEffect(() => {
    if (index === null && questionnaire) {
      setIndex(resumeIndexOf(questionnaire.questions, answers))
    }
    // answers는 일부러 의존성에서 뺀다 — 답할 때마다 위치가 튀면 안 된다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionnaire, index])

  if (isPending || !questionnaire || index === null) {
    return (
      <Screen header={<TopBar />} center>
        <p className="text-center text-body text-muted">문항을 불러오는 중이에요…</p>
      </Screen>
    )
  }

  const questions = questionnaire.questions
  const question = questions[index]
  const current = answers.find((a) => a.questionId === question.id)
  const selected = current?.optionIds ?? []
  const isLast = index === questions.length - 1

  function goPrev() {
    if (index === null) return
    // 첫 문항에서 뒤로 = 문진을 벗어나는 것이므로 그만두기와 같은 확인을 거친다.
    if (index === 0) {
      setAskingExit(true)
      return
    }
    setIndex(index - 1)
  }

  function goNext() {
    if (index === null) return
    if (isLast) {
      navigate(ROUTES.surveyWaiting)
      return
    }
    setIndex(index + 1)
  }

  return (
    <Screen
      header={
        <TopBar
          onBack={goPrev}
          right={
            <button
              type="button"
              onClick={() => setAskingExit(true)}
              className="text-hint text-muted"
            >
              그만두기
            </button>
          }
        />
      }
      footer={
        <Button disabled={!isAnswered(current)} onClick={goNext}>
          {isLast ? '결과 확인하기' : '다음'}
        </Button>
      }
    >
      <div className="flex flex-col gap-lg pb-lg">
        <ProgressBar current={index + 1} total={questions.length} />

        <h1 className="text-title font-extrabold leading-snug">{question.text}</h1>

        {question.type === 'slider' ? (
          <SliderChoice
            options={question.options}
            selected={selected}
            // 슬라이더는 중단점 **번호(1부터)** 를 함께 저장한다 — 판별 쪽으로는
            // 지문 id가 아니라 이 int가 넘어간다(core/survey/types.ts).
            onChange={(ids) =>
              setAnswer(question.id, ids, question.options.findIndex((o) => o.id === ids[0]) + 1)
            }
          />
        ) : (
          <ChoiceList
            options={question.options}
            selected={selected}
            multiple={question.type === 'multi'}
            onChange={(ids) => setAnswer(question.id, ids)}
          />
        )}

        {question.type === 'multi' ? (
          <p className="text-caption text-faint">해당하는 것을 모두 골라주세요.</p>
        ) : null}
      </div>

      {askingExit ? (
        <ConfirmSheet
          title="문진을 그만두시겠어요?"
          body={`여기까지 답하신 ${answers.length}문항은 저장돼 있어요. 다시 오시면 이어서 하실 수 있습니다.`}
          confirmLabel="그만두기"
          cancelLabel="계속 답할래요"
          onConfirm={() => navigate(ROUTES.surveyIntro)}
          onCancel={() => setAskingExit(false)}
        />
      ) : null}
    </Screen>
  )
}
