import { useState } from 'react'
import { useNavigate } from 'react-router'

import { fetchQuestionnaire } from '../../../core/survey/provider'
import { useSurveyStore, type Gender } from '../../../core/store/survey'
import { Button } from '../../components/Button'
import { Field, SegToggle, TextInput } from '../../components/Form'
import { Screen } from '../../components/Screen'
import { TopBar } from '../../components/TopBar'
import { ROUTES } from '../../routes'
import { useQuery } from '@tanstack/react-query'

// sc_008 문진 설명 + 생년월일·성별·키·몸무게 입력.
//
// 화면설계서 '홈 > TEM문진' #1~#4가 정본이다. 명세서 v5의 sc_008에는 이 입력들이
// 없지만(타이틀·설명·시작버튼뿐), 화면 구성은 설계서를 따른다(결정 #30).
//
// ★ 생년월일·성별은 개인정보다. 여기는 동의(sc_092) 이전이므로 **서버로 보내지 않고
//   클라이언트에만 보관**한다(docs/02_architecture_constraints.md §4). 가입이 끝나는
//   시점에 문진 결과와 함께 한 번에 전송된다.

const GENDERS = ['남성', '여성'] as const

export function SurveyAboutScreen() {
  const navigate = useNavigate()
  const { data: questionnaire } = useQuery({
    queryKey: ['questionnaire'],
    queryFn: fetchQuestionnaire,
  })

  const setProfile = useSurveyStore((s) => s.setProfile)

  const [birthDate, setBirthDate] = useState(useSurveyStore.getState().birthDate)
  const [gender, setGender] = useState<Gender | ''>(useSurveyStore.getState().gender)
  const [heightCm, setHeightCm] = useState(useSurveyStore.getState().heightCm)
  const [weightKg, setWeightKg] = useState(useSurveyStore.getState().weightKg)

  // 키·몸무게는 설계서에도 플레이스홀더만 있고 필수 표시가 없다. 1차에서 쓰는 곳도
  // 없으므로 비워 두고 넘어갈 수 있게 한다.
  const canProceed = birthDate !== '' && gender !== ''

  function handleNext() {
    setProfile({ birthDate, gender, heightCm, weightKg })
    navigate(ROUTES.survey)
  }

  return (
    <Screen
      header={<TopBar />}
      footer={
        <Button disabled={!canProceed} onClick={handleNext}>
          다음
        </Button>
      }
    >
      <div className="flex flex-col gap-lg pb-lg">
        <div className="flex flex-col gap-sm">
          <h1 className="text-title font-extrabold leading-snug">
            시작 전에
            <br />
            조금만 알려주세요
          </h1>
          <p className="text-body text-muted">
            {questionnaire
              ? `${questionnaire.questions.length}문항 · 약 ${questionnaire.estimatedMinutes}분이면 끝나요.`
              : '문항을 불러오는 중이에요…'}
          </p>
        </div>

        <div className="flex flex-col gap-md">
          <Field label="생년월일">
            <TextInput type="date" value={birthDate} onChange={setBirthDate} autoComplete="bday" />
          </Field>
          <Field label="성별">
            <SegToggle options={GENDERS} value={gender} onChange={setGender} />
          </Field>
          <Field label="키" hint="비워두고 넘어가셔도 돼요.">
            <TextInput value={heightCm} onChange={setHeightCm} placeholder="165" unit="cm" numeric maxLength={3} />
          </Field>
          <Field label="몸무게" hint="비워두고 넘어가셔도 돼요.">
            <TextInput value={weightKg} onChange={setWeightKg} placeholder="70" unit="kg" numeric maxLength={3} />
          </Field>
        </div>

        <p className="rounded-md bg-surface p-md text-caption leading-relaxed text-muted">
          입력하신 내용은 <b>가입을 마치기 전까지 이 기기에만</b> 저장돼요. 가입하지 않고
          나가시면 그대로 사라집니다.
        </p>

        {questionnaire?.source === 'dummy' ? (
          // 더미 문항으로 돌고 있다는 사실이 화면에서도 보여야 한다(결정 #24).
          <p className="rounded-md bg-orange-500/10 p-md text-caption text-orange-500">
            ⚠️ 개발용 더미 문항입니다. 실제 문진 문항이 아니에요.
          </p>
        ) : null}
      </div>
    </Screen>
  )
}
