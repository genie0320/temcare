import { useNavigate } from 'react-router'

import { Button } from '../../components/Button'
import { Screen } from '../../components/Screen'
import { ROUTES } from '../../routes'

// sc_093 접근권한 안내 — OS 권한 요청 전 사전 고지. 최초 1회.
//
// 1차는 웹이라 실제로 요청할 OS 권한이 없다(푸시는 2차, 삼성헬스 연동은 범위 밖).
// 그래도 화면을 두는 이유: 앱스토어 심사 가이드가 권장하는 절차이고, RN 전환 시
// 여기가 네이티브 권한 요청을 붙이는 자리가 되기 때문이다.
//
// 📌 요청 권한 최종 목록·안내 문구는 미확정(PPT SIGNUP-03 #3 "[확인필요]").

const PERMISSIONS = [
  {
    icon: '🔔',
    name: '알림',
    required: '선택',
    reason: '체질에 맞는 처방과 공지를 알려드릴 때 사용해요.',
  },
]

export function PermissionsScreen() {
  const navigate = useNavigate()

  return (
    <Screen
      footer={
        <Button onClick={() => navigate(ROUTES.result, { replace: true })}>
          확인했어요
        </Button>
      }
    >
      <div className="flex flex-1 flex-col justify-center gap-lg py-xl">
        <div className="flex flex-col gap-sm">
          <h1 className="text-title font-extrabold leading-snug">
            이런 권한을
            <br />
            사용하게 돼요
          </h1>
          <p className="text-body text-muted">선택 권한은 허용하지 않아도 서비스를 쓰실 수 있어요.</p>
        </div>

        <div className="flex flex-col gap-sm">
          {PERMISSIONS.map((permission) => (
            <div key={permission.name} className="flex gap-md rounded-md bg-surface p-md">
              <span className="text-title">{permission.icon}</span>
              <div className="flex flex-col gap-xs">
                <span className="text-body font-bold">
                  {permission.name}
                  <span className="ml-xs text-caption font-normal text-faint">[{permission.required}]</span>
                </span>
                <span className="text-hint text-muted">{permission.reason}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Screen>
  )
}
